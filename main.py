import atexit
from psychopy import visual, event, core, logging
import time
import pygame
from os.path import join
from os import  remove, listdir
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
if config['GENERATE_FIX_SOUND']:
    sound_generator(name=join('sounds', 'fixsound.wav'), sample_rate=config['FIX_SAMPLE_RATE'],
                    duration=config['FIX_TIME'], frequency=config['FIX_FREQUENCY'], wave_type=config['WAVE_TYPE'])

# generate standard sound
if config['GENERATE_STANDART_SOUND']:
    sound_generator(name=join('sounds', 'standard.wav'), sample_rate=config['S_SAMPLE_RATE'],
                    duration=config['S_TIME'], frequency=config['S_FREQUENCY'], wave_type=config['WAVE_TYPE'])

# generate screen
SCREEN_RES = get_screen_res()
window = visual.Window(SCREEN_RES, fullscr=True, monitor='testMonitor', units='pix',
                       screen=0, color='Gainsboro', winType='pygame')
FRAMES_PER_SEC = get_frame_rate(window)
mouse = event.Mouse(visible=False)

help_text = "Lewa strzałka (pierwszy dźwięk wyższy), prawa strzałka (drugi dźwięk wyższy)"
help_line = visual.TextStim(win=window, antialias=True, font=u'Arial',
                            text=help_text, height=config['TEXT_SIZE'],
                            wrapWidth=SCREEN_RES[0], color=u'black',
                            pos=(0, -300))

response_clock = core.Clock()


def run_trial(n):
    # prepare trail
    if config['TASK_TYPE'] == 'FREQUENCY':
        if random.random() > 0.5:
            higher = 'comparison'
            sound_generator(name=join('sounds', 'comparison{}.wav'.format(i)), sample_rate=config['S_SAMPLE_RATE'],
                            duration=config['S_TIME'], frequency=config['S_FREQUENCY'] + n, wave_type=config['WAVE_TYPE'])
        else:
            higher = 'standard'
            sound_generator(name=join('sounds', 'comparison{}.wav'.format(i)), sample_rate=config['S_SAMPLE_RATE'],
                            duration=config['S_TIME'], frequency=config['S_FREQUENCY'] - n, wave_type=config['WAVE_TYPE'])

        sounds = [(join('sounds', 'comparison{}.wav'.format(i)  ), config['VOLUME'], "comparison"),
                  (join('sounds', 'standard.wav'), config['VOLUME'], "standard")]
        random.shuffle(sounds)
    elif config['TASK_TYPE'] == 'VOLUME':
        if random.random() > 0.5:
            higher = 'comparison'
            change = n
        else:
            higher = 'standard'
            change = -n
        sounds = [(join('sounds', 'standard.wav'), config['VOLUME'] + change, "comparison"),
                  (join('sounds', 'standard.wav'), config['VOLUME'], "standard")]
        random.shuffle(sounds)
    else:
        raise Exception("unknown TASK_TYPE")

    stim_time = config['S_TIME'] + config['RTIME']
    rt = None
    acc = 0

    # play trial
    help_line.setAutoDraw(True)
    window.flip()

    if config['PLAY_FIX_SOUND']:
        play_sound(join('sounds', 'fixsound.wav'), volume=config['VOLUME'])
        time.sleep(config['S_TIME'])
    time.sleep(config['DELAY'])

    play_sound(sounds[0][0], sounds[0][1])
    time.sleep(config['S_TIME'] + config['ISI'])

    play_sound(sounds[1][0], sounds[1][1])
    response_clock.reset()

    while response_clock.getTime() < stim_time:
        check_exit()
        keys = event.getKeys(keyList=KEYS)
        if keys:
            rt = response_clock.getTime()
            resp = sounds[KEYS.index(keys[0])][2]
            acc = 1 if resp == higher else -1
            break
    help_line.setAutoDraw(False)
    window.flip()
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
                      step_down=config['STEP'], min_level=config["MIN_LEVEL"], max_level=config['MAX_LEVEL'])

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

    RESULTS.append([i, 1, acc, rt, stim_time, n, reversal, rev_count_val])
    experiment.set_corr(acc)

show_info(window, join('.', 'messages', "end.txt"), text_size=config['TEXT_SIZE'], screen_width=SCREEN_RES[0])
pygame.quit()

for file in listdir('sounds'):
    remove('sounds/'+file)
