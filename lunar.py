'''
LastEditors: John
Date: 2023-07-16 13:26:01
LastEditTime: 2023-07-21 21:29:29
Author: John
'''
import os
import sys

from pynput import keyboard
from termcolor import colored

from lib.inter import Inter
from lib.key_validator import KeyValidator


def on_release(key):
    try:
        if key == keyboard.Key.home:
            Aimbot.update_status_aimbot()
        if key == keyboard.Key.end:
            Aimbot.clean_up()
    except NameError:
        pass


def main():
    validator = KeyValidator()
    validator.check_key_file()

    global lunar
    lunar = Aimbot(collect_data="collect_data" in sys.argv)
    lunar.start()


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

    print(colored('''
    | |
    | |    _   _ _ __   __ _ _ __
    | |   | | | | '_ \ / _` | '__|
    | |___| |_| | | | | (_| | |
    \_____/\__,_|_| |_|\__,_|_|

    (Neural Network Aimbot)''', "yellow"))

    path_exists = os.path.exists("lib/data")
    if "collect_data" in sys.argv and not path_exists:
        os.makedirs("lib/data")
    from lib.aimbot import Aimbot
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    main()
