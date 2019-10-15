"""Order Task for fMRI studies. Training version.

This script contains training version of order task used in fMRI study on
numerical skills. Task consists of two conditions sequentially presented in a
block design. Each block is comprised of trials. At each trial, three digits
are presented on a screen. In the control condition subject has to answer
whether certain digit (target) is displayed in a sequence. In the order
condition subject has to determine whether a sequence is ordered (either
increasing or decreasing) or not in order. Digits are loaded from file provided
by the user.

Entire task is comprised of four blocks (2 control and 2 order). First two
blocks contain feedback for participant, last two blocks don't.

Author: Kamil Bonna (bonna@doktorant.umk.pl)
Version: t.3.4

Features:
- adaptivness:
    Feedback disappears when subject has >50% correct responses during demanding
    order condition, and finishes if subject has >66% correct responses in order
    condition only if feedback was not delivered. To minimise frustration of
    subjects during first blocks response time is unlimited. (added 15/10/19)
"""
from psychopy import visual, core, event, gui, data
from random import sample, shuffle

### Settings ###################################################################
# Window (screen)
win_size = [800, 600]
win_color = [-.5, -.5, -.5]
win_screen = 0
win_fullscr = True
win_mouse_visible = False
win_monitor = 'testMonitor'
win_units = 'norm'

# Stimuli
path_log = 'logs_training/'
path_stim = 'stimuli/stimuli_easy.xlsx'
path_feedback_win = 'stimuli/happy2.png'
path_feedback_los = 'stimuli/try_again2.png'
path_instr_con = 'stimuli/instr_con_fmri.png'
path_instr_ord = 'stimuli/instr_ord_fmri.png'
digit_separation = 0.3
digit_height = 0.2
text_separation = 0.2
text_height = 0.2
text_color = [1, 1, 1]
text_fix_height = 0.2
face_size = [7, 7] # in cm

# Keys
key_right = 'm' # Response: yes
key_left = 'z' # Response: no
key_quit = 'q'

# Timing (in seconds)
time_fix = 4
time_info = 4
time_digit = [float("inf"), float("inf"), 3, 2, 2, 2, 2, 2]
time_feedback = 2

# wait_till_end has to be False if coresponing time_digit is inf!
wait_till_end = [False, False, True, True, True, True, True, True]
max_n_blocks = 8

### Global keys ################################################################
event.globalKeys.clear()
event.globalKeys.add(
    key=key_quit,
    func=core.quit)

### Task structure #############################################################
# Import stimuli from file
stim = data.importConditions(path_stim, returnFieldNames=False)

# Randomize block order for both conditions
blorder_o = sample([i for i in range(1, 5)], 4) * 2
blorder_c = sample([i for i in range(1, 5)], 4) * 2

### Dialogue box ###############################################################
dlg = gui.Dlg(title="Order Task Training")
dlg.addText('ENSURE THAT NUM LOCK IS OFF!')
dlg.addText('Subject info')
dlg.addField('Id:')
dlg_data = dlg.show()

if dlg.OK:
    subject_id = dlg_data[0]
    date_str = data.getDateStr()
    filename = 'logs_training/'+ subject_id +'_ot_Dyscalculia_training'
else:
    print('Canceled. Quitting...')
    core.quit()

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
    height=text_height/2,
    wrapWidth=25,
    alignHoriz='center')
face_win = visual.ImageStim(
    win=mywin,
    image=path_feedback_win,
    pos=[0,0],
    size=face_size,
    units='cm')
face_los = visual.ImageStim(
    win=mywin,
    image=path_feedback_los,
    pos=[0,0],
    size=face_size,
    units='cm')
instr = visual.ImageStim(
    win=mywin,
    image=path_instr_con)

### Experiment #################################################################
# Create clocks
timer = core.CountdownTimer()
rtimer = core.Clock() # For reaction time

# Data handlers
exp = data.ExperimentHandler(
    name='ot_Dyscalculia_training',
    version='t.3.3',
    dataFileName=filename,
    extraInfo={'subject_id': subject_id})

# Ask participant for readiness
text_center.setText('Gdy będziesz gotowy(-wa) naciśnij dowolny przycisk.')
text_center.draw(); mywin.flip()
event.waitKeys()
print('Participant {} is ready.'.format(subject_id))

### Task begins ################################################################

block = 0
stop_cond = False
feedback = True
accu = []

while (stop_cond == False) and (block <= max_n_blocks-1):

    block += 1

    for condition in ['control', 'order']:

        print(f'\nStarting feedback {condition} block {block}\n')

        ### Info screen ########################################################
        if condition =='control':   instr.setImage(path_instr_con)
        else:                       instr.setImage(path_instr_ord)
        timer.reset(time_info)
        instr.draw(); mywin.flip()

        ### Trial loop creation ################################################
        if condition == 'control':  blorder = blorder_c[block]
        else:                       blorder = blorder_o[block]

        trials = data.TrialHandler(
            trialList=[row for row in stim if row['block'] == blorder],
            nReps=1,
            method='random')

        # Pin existing loop to ExperimentHandler
        exp.addLoop(trials)

        # Wait till the end of info screen time
        while timer.getTime() > 0:
            instr.draw(); mywin.flip()

        # Adaptive check #######################################################
        if condition == 'order':    corr_sum = 0

        ### Begin block ########################################################
        for thisTrial in trials:

            ### fixation #######################################################
            timer.reset(t=time_fix)
            while timer.getTime() > 0:
                fix.draw(); mywin.flip()

            ### digits #########################################################
            digit_l.setText(text=thisTrial['digit_l']); digit_l.draw()
            digit_r.setText(text=thisTrial['digit_r']); digit_r.draw()
            digit_c.setText(text=thisTrial['digit_c']); digit_c.draw()
            mywin.flip()
            timer.reset(t=time_digit[block-1])
            rtimer.reset()

            response = event.waitKeys(
                maxWait=time_digit[block-1],
                keyList=[key_left, key_right],
                timeStamped=rtimer,
                clearEvents=True)

            if wait_till_end[block-1]:
                while timer.getTime() > 0:
                    digit_l.draw(); digit_r.draw(); digit_c.draw(); mywin.flip()

            ### analyze response ###############################################
            if response == None:
                rt = 0
                correct = -1
                keypressed = None
            elif response[0][0] == key_right:
                keypressed = key_right
                if condition == 'control':
                    correct = int(thisTrial['is_target'] == 1)
                    rt = response[0][1]
                else: #condition == 'order':
                    correct = int(abs(thisTrial['is_order']) == 1)
                    rt = response[0][1]
            elif response[0][0] == key_left:
                keypressed = key_left
                if condition == 'control':
                    correct = int(thisTrial['is_target'] == 0)
                    rt = response[0][1]
                else: #condition == 'order':
                    correct = int(thisTrial['is_order'] == 0)
                    rt = response[0][1]

            # Save responses in TrialHandler
            trials.addData('rt', rt)
            trials.addData('correct', correct)
            trials.addData('response', keypressed)
            trials.addData('condition', condition)
            exp.nextEntry()

            ### feedback screen (only in first block) ##########################
            if feedback:
                timer.reset(time_feedback)
                if correct == 1:
                    while timer.getTime() > 0:
                        face_win.draw(); mywin.flip()
                else:
                    while timer.getTime() > 0:
                        face_los.draw(); mywin.flip()

            # Adaptive check ###################################################
            if condition == 'order':
                if correct == 1:
                    corr_sum += 1

            # Informations for researcher
            print(f'<> {thisTrial["digit_l"]} {thisTrial["digit_c"]} {thisTrial["digit_r"]} <>')
            print(f'Correct={correct}, RT={rt:.3f}, keys={keypressed}')

        # Adaptation ###########################################################
        if condition == 'order':
            # End task when accuracy >= 66% without feedback
            if corr_sum >= 8 and feedback == False:
                stop_cond = True
            # Turn off feedback when accuracy >= 50% (from second block)
            if corr_sum >= 6 and block >= 2:    feedback = False
            else:                               feedback = True

            accu.append(corr_sum / 12)

# 'Thank you' screen after task
timer.reset(time_info)
text_center.setText('Dziękujemy za udział w badaniu!')
while timer.getTime() > 0:
    text_center.draw(); mywin.flip()
print('\nTask ended. Saving logs.')
print('\nAccuracy in order conditions:')
for i, acc in enumerate(accu):
    print(f'Block {i}: accuracy = {acc}')

### Save data ##################################################################
# Behavioral part
exp.saveAsWideText(
    fileName=filename,
    delim=',')
