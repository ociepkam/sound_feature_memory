import atexit
from psychopy import visual, event, core, logging
import time
import pygame
from os.path import join
import csv
import random

from sources.experiment_info import experiment_info
from sources.load_data import load_config
from sources.screen import get_screen_res, get_frame_rate
from sources.show_info import show_info
from sources.check_exit import check_exit
from sources.adaptives.NUpNDown import NUpNDown
from sources.sound_generator import play_sound, sound_generator

part_id, part_sex, part_age, date = experiment_info()
NAME = "{}_{}_{}".format(part_id, part_sex, part_age)

RESULTS = list()
KEYS = ['left', 'right']

# TODO: jakie parametry
RESULTS.append(['NR', 'EXPERIMENTAL', 'ACC', 'RT', 'TIME', 'LEVEL', 'REVERSAL', 'REVERSAL_COUNT'])

RAND = str(random.randint(100, 999))

logging.LogFile(join('.', 'results', 'logging', NAME + '_' + RAND + '.log'), level=logging.INFO)


@atexit.register
def save_beh():
    logging.flush()
    with open(join('results', 'behavioral_data', 'beh_{}_{}.csv'.format(NAME, RAND)), 'w') as csvfile:
        beh_writer = csv.writer(csvfile)
        beh_writer.writerows(RESULTS)


config = load_config()

# generate fix sound
sound_generator(name=join('sounds', 'fixsound.wav'), sample_rate=config['FIX_SAMPLE_RATE'],
                duration=config['FIX_TIME'], frequency=config['FIX_FREQUENCY'], wave_type=config['WAVE_TYPE'])

# generate standard sound
sound_generator(name=join('sounds', '_standard.wav'), sample_rate=config['S_SAMPLE_RATE'],
                duration=config['S_TIME'], frequency=config['S_FREQUENCY'], wave_type=config['WAVE_TYPE'])

# generate screen
SCREEN_RES = get_screen_res()
window = visual.Window(SCREEN_RES, fullscr=True, monitor='testMonitor', units='pix',
                       screen=0, color='Gainsboro', winType='pygame')
FRAMES_PER_SEC = get_frame_rate(window)
mouse = event.Mouse(visible=False)

response_clock = core.Clock()


def run_trial(n):
    # prepare trail
    if random.random() > 0.5:
        higher = 'comparison'
        sound_generator(name=join('sounds', '_comparison.wav'), sample_rate=config['S_SAMPLE_RATE'],
                        duration=config['S_TIME'], frequency=config['S_FREQUENCY'] + n, wave_type=config['WAVE_TYPE'])
    else:
        higher = 'standard'
        sound_generator(name=join('sounds', '_comparison.wav'), sample_rate=config['S_SAMPLE_RATE'],
                        duration=config['S_TIME'], frequency=config['S_FREQUENCY'] - n, wave_type=config['WAVE_TYPE'])

    sounds = [join('sounds', '_comparison.wav'), join('sounds', '_standard.wav')]
    random.shuffle(sounds)
    stim_time = config['S_TIME'] + config['RTIME']
    rt = None
    acc = 0

    # play trial
    play_sound(join('sounds', 'fixsound.wav'))
    time.sleep(config['S_TIME'] + config['DELAY'])

    play_sound(sounds[0])
    time.sleep(config['S_TIME'] + config['ISI'])

    play_sound(sounds[1])
    response_clock.reset()

    while response_clock.getTime() < stim_time:
        check_exit()
        keys = event.getKeys(keyList=KEYS)
        if keys:
            rt = response_clock.getTime()
            resp = sounds[KEYS.index(keys[0])].split('.')[0].split('_')[-1]
            acc = 1 if resp == higher else -1
            break

    time.sleep(config['JITTER_TIME'])

    return acc, rt, stim_time, n

pygame.init()
# TRAINING
show_info(window, join('.', 'messages', "instruction1.txt"), text_size=config['TEXT_SIZE'], screen_width=SCREEN_RES[0])

i = 1
for elem in config['TRAINING_TRIALS']:
    for trail in range(elem['n_trails']):
        acc, rt, stim_time, n = run_trial(n=elem['level'])
        RESULTS.append([i, 0, acc, rt, stim_time, n, 0, 0])
        i += 1

# EXPERIMENT
show_info(window, join('.', 'messages', "instruction2.txt"), text_size=config['TEXT_SIZE'], screen_width=SCREEN_RES[0])

experiment = NUpNDown(start_val=config['START_LEVEL'], max_revs=config['MAX_REVS'], step_up=config['STEP'],
                      min_level=config["MIN_LEVEL"], max_level=config['MAX_LEVEL'])

old_rev_count_val = -1
for i, soa in enumerate(experiment, i):
    pass
    if i > config['MAX_TRIALS']:
        break
    acc, rt, stim_time, n = run_trial(soa)
    level, reversal, revs_count = map(int, experiment.get_jump_status())
    if old_rev_count_val != revs_count:
        old_rev_count_val = revs_count
        rev_count_val = revs_count
    else:
        rev_count_val = '-'

    RESULTS.append([config['TRAINING_TRIALS'] + i, 1, acc, rt, stim_time, n, reversal, rev_count_val])
    experiment.set_corr(acc)

show_info(window, join('.', 'messages', "end.txt"), text_size=config['TEXT_SIZE'], screen_width=SCREEN_RES[0])
pygame.quit()