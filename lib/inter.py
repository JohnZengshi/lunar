
import ctypes
from lib.interception_py.consts import interception_filter_key_state, interception_filter_mouse_state
from lib.interception_py.interception import interception
from lib.interception_py.stroke import mouse_stroke
from pynput import keyboard


class Inter:
    SCANCODE_ESC = 0x01
    init = False

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
            stroke: mouse_stroke = self.inter.receive(device)
            self.inter.send(device, stroke)
            Inter.init = True
            # print(stroke.x, stroke.y)
            if stroke is None or Inter.init == False:
                break

        print("inter is quite!")
        self.inter._destroy_context()

    def on_release(key):
        try:
            if key == keyboard.Key.end:
                Inter.init = False
        except NameError:
            pass
