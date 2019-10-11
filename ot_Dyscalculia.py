"""Order Task for fMRI studies.

This script contains order task used in fMRI study on numerical skills. Task
consists of two conditions sequentially presented in a block design. Each block
is comprised of trials. At each trial, three digits are presented on a screen.
In the control condition subject has to answer whether certain digit (target) is
displayed in a sequence. In the order condition subject has to determine whether
a sequence is ordered (either increasing or decreasing) or not in order. Digits
are loaded from file provided by the user.

Reference:
    Kucian et al. "Mental number line training in children with developmental
    dyscalculia." Neuroimage 57.3 (2011): 782-795.

Author: Kamil Bonna (bonna@doktorant.umk.pl)
Version: 3.3
Updates:
    26-03-2019: version 3.2 released
    -> changed entire timing method to non-slip timing
    -> glob_clock is used just for post experiment checking of synchronisation
    -> fmri_clock is directly correlated with scanner pulse timing and it is
    meant to be used in GLM model analysis
    01-04-2019: version 3.3 released
    -> changed instruction screens from automatically generated to loaded from
    png files sitting within /stimulus folder
"""
from psychopy import visual, core, event, gui, data
from random import sample, randint, shuffle, seed
import pandas as pd
import numpy as np
seed()

### Functions ##################################################################
def generate_isi(n_trials, min_frames, max_frames, chunk):
    """Generates random isi as number of frames. Used to generate isi for one
    block of task. Enables randomized isi, while preserving fixed block length.

    Parameters:
        n_trials (int): Number of trials requiring isi.
        min_frames (int): Minimum number of isi frames.
        max_frames (int): Maximum number of isi frames.
        chunk (int): Specifies a number of isi frames step size. Possible isi
            values will be min_frames + k * chunk, where k is positive integer.

    Returns:
        frames (np.array): isi values for all trials.

    Note:
        Mean number of isi frames for all trials will be equal to
            (min_frames + max_frames) / 2. This ensures blocks of equal length.

    Raises:
        ValueError: If max_frames is not greater than min_frames or if
            (max_frames - min_frames) is not divisible by chunk value or if
            mean number of frames is not an integer.
    """
    if max_frames <= min_frames:
        raise ValueError('max_frames should be greater than min_frames.')
    if (max_frames - min_frames) % chunk != 0:
        raise ValueError('step size should allow to reach exact value of '
            + 'max_frames from min_frames.')
    if (max_frames - min_frames) % 2 != 0:
        raise ValueError('mean number of frames should be an integer')

    frames = [min_frames for _ in range(n_trials)]
    remaining_frames = int(n_trials * (max_frames - min_frames) / 2)
    while remaining_frames > 0:
        ind = randint(0, n_trials - 1)
        if frames[ind] + chunk <= max_frames:
            frames[ind] += chunk
            remaining_frames -= chunk
    frames = np.array(frames)
    return frames

def generate_onsets(isi_seconds, time_block, time_info, n_trials):
    '''This function takes isi durations (represented as number of frames)
    generated for all trials and convert it into fixed task onsets for fixation
    and digit events.

    Parameters:
        isi_seconds (list of np.array's): List of length equal to number of
            blocks, each element contains np.array of length equal to number of
            trials within block; elements of these arrays are isi in secondns.
        time_block (float): Block duration in seconds.
        time_info (float): Duration in seconds of instruction screen displayed
            before eachblock.
        n_trials (int): Number of trials per block.

    Returns:
        onset_fix (list of np.array's): Contains onset times for fixation
            events. It's entries correspond to isi_seconds entries.
        onset_dig (list of np.array's): Contains onset times for digit events.
            It's entries correspond to isi_seconds entries.
    '''
    onset_fix, onset_dig = [], []

    for idb, isi_dur in enumerate(isi_seconds):
        # Time padding added before each block
        padding = time_info * (idb + 1) + time_block * idb
        # Cumulated and shifted isi
        isi_cum = np.concatenate(([0], np.cumsum(isi_dur)[:-1]))
        # Cumulated digit time
        dig_cum = np.arange(0, time_digit * n_trials, time_digit)

        onset_fix.append(isi_cum + dig_cum + padding)
        onset_dig.append(isi_cum + dig_cum + isi_dur + padding)

    return onset_fix, onset_dig

def seconds2frames(time, refresh_rate):
    '''Converts time in seconds to number of frames ensuring even number of
    frames.

    Parameters:
        time (float): Time in seconds.
        refresh_rate (int): Screen refresh rate in Hz.

    Returns:
        n_frames (int): Number of frames.
    '''
    if type(refresh_rate) is not int:
        raise TypeError('Refresh rate should be integer.')
    if time < 0 or refresh_rate < 0:
        raise ValueError('Input values should be positive.')
    n_frames = refresh_rate * time
    if not float(n_frames).is_integer():
        raise ValueError(f'time should be multiple of {1/refresh_rate}')
    else:
        return(int(n_frames))

def frames2seconds(frames, refresh_rate):
    '''Converts number of frames to time in seconds.'''
    return (frames / refresh_rate)

def save_pulses(pulses, filename):
    '''Saves pulse onsets and spacing between them into csv file'''
    if pulses:
        puldur = [p1-p2 for p1, p2 in zip(pulses[1:], pulses[:-1])]
        puldur = [0] + puldur
        df = pd.DataFrame(
            {'onset': pulses,
             'spacing': puldur})
        df.index = np.arange(1, len(df)+1)
        df.to_csv(filename + '_pulse.csv', sep=",", columns=['onset','spacing'])

def getpulse():
    '''Collecting scanner pulses'''
    global pulses
    global clock
    pulses.append(glob_clock.getTime())

### Settings ###################################################################
# Window (screen)
win_size = [800, 600]
win_color = [-.5, -.5, -.5]
win_screen = 1
win_fullscr = True
win_mouse_visible = False
win_monitor = 'testMonitor'
win_units = 'norm'

# Stimuli
path_log = 'logs/'
path_stim = 'stimuli/stimuli_easy.xlsx'
path_instr_con = 'stimuli/instr_con_fmri.png'
path_instr_ord = 'stimuli/instr_ord_fmri.png'
digit_separation = 0.3
digit_height = 0.2
text_separation = 0.2
text_height = 0.2
text_color = [1, 1, 1]
text_fix_height = 0.2

# Keys
key_right = 'd' # Response: yes
key_left = 'a' # Response: no
key_pulse = 's'
key_quit = 'q'

# Timing (in seconds)
time_digit = 2
time_info = 4
time_range_isi = [3, 5]
time_chunk_isi = 0.5
refresh_rate = 60 # Hz
n_block = 4
n_trials = 12

### Global keys ################################################################
event.globalKeys.clear()
event.globalKeys.add(
    key=key_quit,
    func=core.quit)
event.globalKeys.add(
    key=key_pulse,
    func=getpulse,
    name='record_fmri_pulses')

### Task structure #############################################################
# Randomize intervals (measured as number of frames)
n_refresh_info = seconds2frames(
    time=time_info,
    refresh_rate=refresh_rate)
n_chunk_isi = seconds2frames(
    time=time_chunk_isi,
    refresh_rate=refresh_rate)
n_range_isi = [seconds2frames(
    time=time,
    refresh_rate=refresh_rate)
    for time in time_range_isi]
isi = [generate_isi(n_trials=n_trials, chunk=n_chunk_isi,
                    min_frames=n_range_isi[0], max_frames=n_range_isi[1])
                    for _ in range(2 * n_block)]

# Calculate fixed onsets of all task events (v3.2)
time_block = n_trials * (np.mean(time_range_isi) + time_digit) # Block duration
isi_seconds = [frames2seconds(isi_block, refresh_rate) for isi_block in isi]
onset_fix, onset_dig = generate_onsets(
    isi_seconds=isi_seconds,
    time_block=time_block,
    time_info=time_info,
    n_trials=n_trials)

# Import stimuli from file
stim = data.importConditions(path_stim, returnFieldNames=False)

# Randomize block order for both conditions
blorder_o = sample([i for i in range(1, n_block + 1)], n_block)
blorder_c = sample([i for i in range(1, n_block + 1)], n_block)

# Scanner pulses
pulses = []

### Objects ####################################################################
mywin = visual.Window(
    size=win_size,
    fullscr=win_fullscr,
    color=win_color,
    monitor=win_monitor,
    screen=win_screen,
    units='norm',
    winType='pyglet')
mywin.mouseVisible = win_mouse_visible
fix = visual.TextStim(
    win=mywin,
    text='+',
    pos=[0, 0],
    color=text_color,
    height=text_fix_height)
digit_l = visual.TextStim(
    win=mywin,
    text='',
    pos=[-digit_separation, 0],
    color=text_color,
    height=digit_height)
digit_r = visual.TextStim(
    win=mywin,
    text='',
    pos=[digit_separation, 0],
    color=text_color,
    height=digit_height)
digit_c = visual.TextStim(
    win=mywin,
    text='',
    pos=[0, 0],
    color=text_color,
    height=digit_height)
text_center = visual.TextStim(
    win=mywin,
    text='',
    pos=[0, 0],
    color=text_color,
    height=text_height/3,
    wrapWidth=25,
    alignHoriz='center')
instr = visual.ImageStim(
    win=mywin,
    image=path_instr_con)

### Experiment #################################################################
# Create clocks
glob_clock = core.MonotonicClock() # Just for post experimental check
fmri_clock = core.Clock() # Main clock synchronised with fMRI trigger

# Dialogue box
dlg = gui.Dlg(title="Order Task (Dyscalculia) v3.2")
dlg.addText('ENSURE THAT NUM LOCK IS OFF!')
dlg.addText('Subject info')
dlg.addField('Id:')
dlg_data = dlg.show()

if dlg.OK:
    subject_id = dlg_data[0]
    date_str = data.getDateStr()
    filename = 'logs/'+ subject_id +'_ot_Dyscalculia'
else:
    print('Canceled. Quitting...')
    core.quit()

# Data handlers
exp = data.ExperimentHandler(
    name='ot_Dyscalculia',
    version='3.2',
    dataFileName=filename,
    extraInfo={'subject_id': subject_id})

# Ask participant for readiness
text_center.setText('Gdy będziesz gotowy(-wa) naciśnij dowolny przycisk.')
text_center.draw(); mywin.flip()
event.waitKeys(keyList=[key_left, key_right])
print('Participant {} is ready.'.format(subject_id))
text_center.setText('Zadanie rozpocznie się za moment.')
text_center.draw(); mywin.flip()

# Wait for the first scanner pulse
print('\nWaiting for fMRI trigger...\n')
event.waitKeys(keyList=[key_pulse])
fmri_clock.reset() # Synchronisation with first pulse

# Begin pair of blocks
idb = -1 # Indexing single blocks
for block in range(n_block):

    # Begin single block
    for condition in ['control','order']:
        idb += 1

        print(f'\nStarting {block + 1} {condition} block...\n')

        ### Info screen ########################################################
        if condition =='control':   instr.setImage(path_instr_con)
        else:                       instr.setImage(path_instr_ord)

        exp.addData('onset_info', fmri_clock.getTime())
        exp.addData('onset_info_glob', glob_clock.getTime())
        exp.nextEntry()
        instr.draw(); mywin.flip()

        ### Trial loop creation (may take a while) #############################
        if condition == 'control':  blorder = blorder_c[block]
        else:                       blorder = blorder_o[block]

        trialList = [row for row in stim if row['block'] == blorder]
        shuffle(trialList)
        trials = data.TrialHandler(
            trialList=trialList,
            nReps=1,
            method='sequential')

        # Set onsets
        for idx, trial in enumerate(trials.trialList):
            trial.update({'isi_seconds': isi_seconds[idb][idx]})
            trial.update({'onset_fix_plan': onset_fix[idb][idx]})
            trial.update({'onset_dig_plan': onset_dig[idb][idx]})
            trial.update({'condition': condition})

        # Pin existing loop to ExperimentHandler
        exp.addLoop(trials)

        # Wait till the end of info screen time
        while fmri_clock.getTime() < onset_fix[idb][0]:
            instr.draw(); mywin.flip()

        # Begin block
        for thisTrial in trials:

            ### fixation #######################################################
            exp.addData('onset_fix', fmri_clock.getTime())
            exp.addData('onset_fix_glob', glob_clock.getTime())

            while fmri_clock.getTime() < thisTrial['onset_dig_plan']:
                fix.draw()
                mywin.flip()

            ### digits #########################################################
            digit_l.setText(text=thisTrial['digit_l']); digit_l.draw()
            digit_r.setText(text=thisTrial['digit_r']); digit_r.draw()
            digit_c.setText(text=thisTrial['digit_c']); digit_c.draw()

            trials.addData('onset_dig', fmri_clock.getTime())
            trials.addData('onset_dig_glob', glob_clock.getTime())
            rt_onset = fmri_clock.getTime() # For RT calculation

            mywin.flip()

            response = event.waitKeys(
                maxWait=time_digit,
                keyList=[key_left, key_right],
                timeStamped=fmri_clock,
                clearEvents=True)

            while fmri_clock.getTime() < thisTrial['onset_dig_plan']+time_digit:
                digit_l.draw()
                digit_r.draw()
                digit_c.draw()
                mywin.flip()

            ### analyze response ###############################################
            if response == None:
                rt = 0
                correct = -1
                keypressed = None
            elif response[0][0] == key_right:
                keypressed = key_right
                if condition == 'control':
                    correct = int(thisTrial['is_target'] == 1)
                    rt = response[0][1] - rt_onset
                else: #condition == 'order':
                    correct = int(abs(thisTrial['is_order']) == 1)
                    rt = response[0][1] - rt_onset
            elif response[0][0] == key_left:
                keypressed = key_left
                if condition == 'control':
                    correct = int(thisTrial['is_target'] == 0)
                    rt = response[0][1] - rt_onset
                else: #condition == 'order':
                    correct = int(thisTrial['is_order'] == 0)
                    rt = response[0][1] - rt_onset

            # Save responses in TrialHandler
            trials.addData('rt', rt)
            trials.addData('correct', correct)
            trials.addData('response', keypressed)
            exp.nextEntry()

            # Informations for researcher
            print(f'<> {thisTrial["digit_l"]} {thisTrial["digit_c"]} {thisTrial["digit_r"]} <>')
            print(f'Correct={correct}, RT={rt:.3f}, keys={keypressed}')

# 'Thank you' screen after task
text_center.setText('Dziękujemy za udział w badaniu!')
for frame in range(n_refresh_info):
    text_center.draw()
    mywin.flip()
print('\nTask ended. Saving logs.')

### Save data ##################################################################
# Behavioral part
exp.saveAsWideText(
    fileName=filename,
    delim=',')
# Scanner part
save_pulses(pulses, filename)
