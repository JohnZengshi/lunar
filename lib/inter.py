'''
LastEditors: John
Date: 2023-07-18 10:06:51
LastEditTime: 2023-07-25 16:29:22
Author: John
'''

import ctypes
from lib.interception_py.consts import interception_filter_key_state, interception_filter_mouse_state
from lib.interception_py.interception import interception
from lib.interception_py.stroke import mouse_stroke
from pynput import keyboard


class Inter:
    SCANCODE_ESC = 0x01
    init = False
    mdevice = 10

    record = False

    def __init__(self) -> None:
        self.inter = interception()

        self.inter.set_filter(
            interception.is_mouse, interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_MOVE.value)
        self.inter.set_filter(interception.is_keyboard, interception_filter_key_state.INTERCEPTION_FILTER_KEY_UP.value |
                              interception_filter_key_state.INTERCEPTION_FILTER_KEY_DOWN.value)
        listener = keyboard.Listener(on_release=Inter.on_release)
        listener.start()

    def start(self):
        while True:
            device = self.inter.wait()
            # print(device)
            if interception.is_mouse(device):
                Inter.mdevice = device
            stroke: mouse_stroke = self.inter.receive(device)
            self.inter.send(device, stroke)
            Inter.init = True
            if interception.is_mouse(device) and Inter.record:
                print(stroke.x, stroke.y)
            if stroke is None or Inter.init == False:
                break

        print("inter is quite!")
        self.inter._destroy_context()

    def on_release(key):
        try:
            if key == keyboard.Key.end:
                Inter.init = False
            # elif key == keyboard.Key.f8:
            #     Inter.record = True
            #     print("开始记录......")
            # elif key == keyboard.Key.f9:
            #     Inter.record = False
            #     print("停止记录......")
        except NameError:
            pass
