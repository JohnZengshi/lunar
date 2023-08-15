'''
LastEditors: John
Date: 2023-07-22 13:59:14
LastEditTime: 2023-07-24 23:16:15
Author: John
'''
import cv2 as cv
from time import time
import keyboard
import mouse

from wincap import WinCap

# initialize wincap
wincap = WinCap(None, 640, True)

# State
STOP = 'f12'
GATHER = 'f10'
gatherDataset = False
active = True
last_ss = time()


def on_stop():
    global active
    active = False
    print('Stopping code!')


def toggleGather():
    global gatherDataset
    gatherDataset = not gatherDataset
    if gatherDataset:
        print('Gathering dataset to folder: ./images/')
    else:
        print('Stopped gathering. Resume with {}'.format(GATHER))


def take_ss():
    global last_ss, gatherDataset
    if (gatherDataset and time() - last_ss > 5):  # 10s cooldown on ss
        last_ss = time()
        wincap.save_ss()


# def on_ctrl_press(event):
#     if event.name == 'ctrl':
#         take_ss()


# Hooks
keyboard.add_hotkey(STOP, on_stop)
keyboard.add_hotkey(GATHER, toggleGather)
# mouse.on_click(take_ss) # this would fire after button is raised up again - it is abit too late.
mouse.on_button(take_ss, buttons=[mouse.X2], types=[mouse.DOWN])
# keyboard.on_press(on_ctrl_press)

print('STOP = {}'.format(STOP))
print('Toggle Gather = {}'.format(GATHER))

while (active):
    # press 'q' to exit
    # waits 25ms every loop to process key press
    if cv.waitKey(25) & 0xFF == ord('q'):
        cv.destroyAllWindows()
        break

cv.destroyAllWindows()
print('End.')
