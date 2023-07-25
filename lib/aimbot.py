import ctypes
import random
import threading
from typing import Any, Callable, List
import cv2
import json
import math
import mss
import numpy as np
import os
import sys
import time
import torch
import uuid
import win32api
import tkinter as tk
from tkinter import ttk

from termcolor import colored
from lib.inter import Inter
from lib.interception_py.consts import interception_filter_mouse_state
from lib.interception_py.interception import interception
from lib.interception_py.stroke import mouse_stroke

# from lib.memory import SharedMemoryWriter

DEFAULT_AIM_WIDTH = 64
DEFAULT_AIM_HEIGHT = 128

DEFAULT_TARGET_HEAD_RATIO = 2.7
DEFAULT_TARGET_BODY_RATIO = 3.5

config_file = "lib/config/config.json"


class Aimbot:
    extra = ctypes.c_ulong(0)
    screen = mss.mss()
    pixel_increment = 1  # controls how many pixels the mouse moves for each relative movement

    with open(config_file, 'r') as f:
        setting_config = json.load(f)
    # long_distance_pixel_increment = setting_config['long_distance_pixel_increment']
    # close_distance_pixel_increment = setting_config['close_distance_pixel_increment']
    aimbot_status = colored("ENABLED", 'green')
    half_screen_width = ctypes.windll.user32.GetSystemMetrics(
        0)/2  # this should always be 960
    half_screen_height = ctypes.windll.user32.GetSystemMetrics(
        1)/2  # this should always be 540
    aimkey = setting_config["aimkey"]
    aimtarget = setting_config["aimtarget"]
    det_box_width = 0

    def __init__(self, box_constant=416, collect_data=False, mouse_delay=0.0001, debug=False):
        # controls the initial centered box width and height of the "Lunar Vision" window
        # controls the size of the detection box (equaling the width and height)
        self.box_constant = box_constant

        print("[INFO] Loading the neural network model")
        self.model = torch.hub.load(
            'lib/yolov5-master', 'custom', path='lib/bestv2.pt', source='local', force_reload=True)
        if torch.cuda.is_available():
            print(colored("CUDA ACCELERATION [ENABLED]", "green"))
        else:
            print(colored("[!] CUDA ACCELERATION IS UNAVAILABLE", "red"))
            print(colored(
                "[!] Check your PyTorch installation, else performance will be poor", "red"))

        # base confidence threshold (or base detection (0-1)
        self.model.conf = 0.45
        self.model.iou = 0.45  # NMS IoU (0-1)
        self.collect_data = collect_data
        self.mouse_delay = mouse_delay
        self.debug = debug

        # 自瞄距离
        self.aim_width, self.aim_height = DEFAULT_AIM_WIDTH, DEFAULT_AIM_HEIGHT

        self.inter = Inter()
        self.inter_thread = threading.Thread(target=self.inter.start)
        self.inter_thread.start()

        print("\n[INFO] PRESS 'HOME' TO TOGGLE AIMBOT\n[INFO] PRESS 'END' TO QUIT")

    def update_status_aimbot():
        if Aimbot.aimbot_status == colored("ENABLED", 'green'):
            Aimbot.aimbot_status = colored("DISABLED", 'red')
        else:
            Aimbot.aimbot_status = colored("ENABLED", 'green')
        sys.stdout.write("\033[K")
        print(f"[!] AIMBOT IS [{Aimbot.aimbot_status}]", end="\r")

    def is_aimbot_enabled():
        return True if Aimbot.aimbot_status == colored("ENABLED", 'green') else False

    def is_targeted():
        return True if win32api.GetKeyState(int(Aimbot.aimkey, 16)) in (-127, -128) else False

    def is_target_locked(x, y):
        # plus/minus 5 pixel threshold
        threshold = 5
        return True if 960 - threshold <= x <= 960 + threshold and 540 - threshold <= y <= 540 + threshold else False

    def move_crosshair(self, x, y):
        if Aimbot.is_targeted() and Aimbot.is_point_inside_rectangle(self, x, y):
            scale = 1
        else:
            return  # TODO

        # if self.aim_width != DEFAULT_AIM_WIDTH:
        #     Aimbot.pixel_increment = Aimbot.close_distance_pixel_increment
        # else:
        #     Aimbot.pixel_increment = Aimbot.long_distance_pixel_increment

        for rel_x, rel_y in Aimbot.interpolate_coordinates_from_center((x, y), scale):
            self.inter.inter.set_filter(
                interception.is_mouse, interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_MOVE.value)

            # print(rel_x, rel_y)
            stroke = mouse_stroke(0, 0, 0, rel_x, rel_y, 0)
            self.inter.inter.send(Inter.mdevice, stroke)

            sleep_time = random.uniform(0.4, 1.4)
            # print("sleepTime:", sleep_time)
            if sleep_time > 1:
                time.sleep(sleep_time / 1_000_000_000_000)

        # generator yields pixel tuples for relative movement
    def interpolate_coordinates_from_center(absolute_coordinates, scale):
        diff_x = (
            absolute_coordinates[0] - Aimbot.half_screen_width) * scale
        diff_y = (
            absolute_coordinates[1] - Aimbot.half_screen_height) * scale

        # 防止抖动
        length = int(math.dist((0, 0), (diff_x, diff_y)))
        if length <= 4:
            return

        # 旧方案
        # print(f"diff_x:{diff_x},diff_y:{diff_y},length:{length}")
        # x = y = sum_x = sum_y = 0
        # pixel_increment = Aimbot.pixel_increment

        # for k in range(0, length):
        #     unit_x = round(diff_x/length)
        #     unit_y = round(diff_y/length)

        #     sum_x += x
        #     sum_y += y

        #     x, y = round(unit_x * k - sum_x), round(unit_y * k - sum_y)
        #     yield x, y

        # 新方案
        # 近距离
        if length <= 30:
            for k in range(0, length):
                x = y = 0
                while x == 0 and y == 0:
                    if diff_x > 0:
                        x = random.choice([0, 1])
                    else:
                        x = random.choice([-1, 0])

                    if diff_y > 0:
                        y = random.choice([0, 1])
                    else:
                        y = random.choice([-1, 0])
                yield x, y
        # 远距离
        else:
            for k in range(0, length):
                x = Aimbot.accelerate_decelerate(k, length)
                y = Aimbot.accelerate_decelerate(k, length)

                if diff_x > 0:
                    x = min(x, diff_x)
                else:
                    x = max(-x, diff_x)

                if diff_y > 0:
                    y = min(y, diff_y)
                else:
                    y = max(-y, diff_y)

                diff_x -= x
                diff_y -= y

                if x != 0 or y != 0:
                    yield round(x), round(y)
    # 判断点是否在自瞄范围内

    def is_point_inside_rectangle(self, x0, y0):
        screen_width = Aimbot.half_screen_width * 2
        screen_height = Aimbot.half_screen_height * 2

        rect_left = (screen_width - self.aim_width) // 2
        rect_right = rect_left + self.aim_width
        rect_top = (screen_height - self.aim_height) // 2
        rect_bottom = rect_top + self.aim_height

        if rect_left <= x0 <= rect_right and rect_top <= y0 <= rect_bottom:
            return True
        else:
            return False

    # 获取加减速值
    def accelerate_decelerate(k, total_steps):
        max_speed = 5
        acceleration_phase = total_steps // 2
        deceleration_phase = total_steps - acceleration_phase

        if k < acceleration_phase:
            speed = (k + 1) * max_speed // acceleration_phase
        else:
            deceleration_steps = k - acceleration_phase
            speed = (deceleration_phase - deceleration_steps) * \
                max_speed // deceleration_phase

        return speed

    def start(self):
        print("[INFO] Beginning screen capture")
        Aimbot.update_status_aimbot()

        detection_box = {'left': int(Aimbot.half_screen_width - self.box_constant//2),  # x1 coord (for top-left corner of the box)
                         # y1 coord (for top-left corner of the box)
                         'top': int(Aimbot.half_screen_height - self.box_constant//2),
                         'width': int(self.box_constant),  # width of the box
                         'height': int(self.box_constant)}  # height of the box
        if self.collect_data:
            collect_pause = 0

        # 定时修改瞄准比值（伪随机决定瞄准位置）
        target_ratio_y = DEFAULT_TARGET_BODY_RATIO
        DEFAULT_TARGET_X = 2
        target_ratio_x = DEFAULT_TARGET_X

        def update_target_ratio():
            nonlocal target_ratio_y
            nonlocal target_ratio_x
            while True:
                target_ratio_y -= 0.1
                if Aimbot.aimtarget == 0:
                    if target_ratio_y <= 2.2:
                        target_ratio_y = DEFAULT_TARGET_HEAD_RATIO
                elif Aimbot.aimtarget == 1:
                    if target_ratio_y <= 2.2:
                        target_ratio_y = DEFAULT_TARGET_BODY_RATIO
                elif Aimbot.aimtarget == 2:
                    if target_ratio_y <= 3.0:
                        target_ratio_y = DEFAULT_TARGET_BODY_RATIO

                if target_ratio_y >= 3.0:
                    target_ratio_x = DEFAULT_TARGET_X + \
                        round(random.uniform(-0.10, 0.10), 2)
                elif self.det_box_width >= 50:
                    target_ratio_x = DEFAULT_TARGET_X + \
                        round(random.uniform(-0.05, 0.05), 2)
                else:
                    target_ratio_x = DEFAULT_TARGET_X

                # print(self.det_box_width)

                time.sleep(2)

        thread_1 = threading.Thread(target=update_target_ratio)
        thread_1.daemon = True
        thread_1.start()

        def update_config_ui():

            # 创建主窗口
            root = tk.Tk()
            root.title("参数设置")

            # def update_long_distance_pixel_increment(value):
            #     Aimbot.long_distance_pixel_increment = float(value)
            #     Aimbot.setting_config['long_distance_pixel_increment'] = value
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.long_distance_pixel_increment,
            #                      label="远距离拉枪速度：", from_=0.1, to=1, callback=update_long_distance_pixel_increment)

            # def update_close_distance_pixel_increment(value):
            #     Aimbot.close_distance_pixel_increment = float(value)
            #     Aimbot.setting_config['close_distance_pixel_increment'] = value
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.close_distance_pixel_increment,
            #                      label="近距离拉枪速度：", from_=0.1, to=2, callback=update_close_distance_pixel_increment)

            def aim_key_on_select(selected_value):
                Aimbot.aimkey = selected_value
                Aimbot.setting_config["aimkey"] = selected_value
                with open(config_file, 'w') as file:
                    json.dump(Aimbot.setting_config, file, indent=4)

            Aimbot.gen_select_ui(root=root, default=Aimbot.aimkey, label="选择自瞄按键：", options=[
                                 "Ctrl", "Shift", "鼠标上侧键", "鼠标下侧键"], values=["0x11", "0x10", "0x06", "0x05"], callback=aim_key_on_select)

            def aim_target_on_select(selected_value):
                Aimbot.aimtarget = selected_value
                Aimbot.setting_config["aimtarget"] = selected_value
                with open(config_file, 'w') as file:
                    json.dump(Aimbot.setting_config, file, indent=4)

            Aimbot.gen_select_ui(root=root, default=Aimbot.aimtarget, label="选择自瞄位置：", options=[
                                 "头部（危险）", "随机头部身体", "身体"], values=[0, 1, 2], callback=aim_target_on_select)

            # 运行主循环
            root.mainloop()

        thread_2 = threading.Thread(target=update_config_ui)
        thread_2.daemon = True
        thread_2.start()

        while True:
            start_time = time.perf_counter()
            frame = np.array(Aimbot.screen.grab(detection_box))
            if self.collect_data:
                orig_frame = np.copy((frame))
            results = self.model(frame)

            if len(results.xyxy[0]) != 0:  # player detected
                least_crosshair_dist = closest_detection = player_in_frame = False
                # iterate over each player detected
                for *box, conf, cls in results.xyxy[0]:
                    x1y1 = [int(x.item()) for x in box[:2]]
                    x2y2 = [int(x.item()) for x in box[2:]]
                    x1, y1, x2, y2, conf = *x1y1, *x2y2, conf.item()
                    height = y2 - y1
                    # offset to roughly approximate the head using a ratio of the height

                    relative_head_X, relative_head_Y = int(
                        (x1 + x2)/target_ratio_x), int((y1 + y2)/2 - height/target_ratio_y)
                    # helps ensure that your own player is not regarded as a valid detection
                    own_player = x1 < 15 or (
                        x1 < self.box_constant/5 and y2 > self.box_constant/1.2)

                    # calculate the distance between each detection and the crosshair at (self.box_constant/2, self.box_constant/2)
                    crosshair_dist = math.dist(
                        (relative_head_X, relative_head_Y), (self.box_constant/2, self.box_constant/2))

                    if not least_crosshair_dist:
                        # initalize least crosshair distance variable first iteration
                        least_crosshair_dist = crosshair_dist

                    if crosshair_dist <= least_crosshair_dist and not own_player:
                        least_crosshair_dist = crosshair_dist
                        closest_detection = {
                            "x1y1": x1y1, "x2y2": x2y2, "relative_head_X": relative_head_X, "relative_head_Y": relative_head_Y, "conf": conf}

                    if not own_player:
                        # draw the bounding boxes for all of the player detections (except own)
                        cv2.rectangle(frame, x1y1, x2y2, (244, 113, 115), 2)
                        # draw the csaonfidence labels on the bounding boxes

                        cv2.putText(frame, f"{int(conf * 100)}%", x1y1,
                                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (244, 113, 116), 2)
                    else:
                        own_player = False
                        if not player_in_frame:
                            player_in_frame = True

                if closest_detection:  # if valid detection exists
                    # draw circle on the head
                    # print(closest_detection)
                    cv2.rectangle(
                        frame, closest_detection["x1y1"], closest_detection["x2y2"], (115, 244, 113), 2)

                    self.det_box_width = closest_detection["x2y2"][0] - \
                        closest_detection["x1y1"][0]
                    det_box_height = closest_detection["x2y2"][1] - \
                        closest_detection["x1y1"][1]
                    if self.det_box_width > DEFAULT_AIM_WIDTH:
                        self.aim_width = self.det_box_width * 3
                        self.aim_height = det_box_height
                    else:
                        self.aim_width = DEFAULT_AIM_WIDTH
                        self.aim_height = DEFAULT_AIM_HEIGHT

                    x1 = int((detection_box["width"] - self.aim_width) // 2)
                    y1 = int((detection_box['height'] - self.aim_height) // 2)
                    x2 = int(x1 + self.aim_width)
                    y2 = int(y1 + self.aim_height)

                    # print(x1, x2, y1, y2)
                    # 在背景图像上绘制矩形
                    cv2.rectangle(frame, (x1, y1), (x2, y2),
                                  (115, 113, 244), 2)

                    cv2.circle(
                        frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), 5, (115, 244, 113), -1)
                    # draw line from the crosshair to the head
                    cv2.line(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), (
                        self.box_constant//2, self.box_constant//2), (244, 242, 113), 2)

                    absolute_head_X, absolute_head_Y = closest_detection["relative_head_X"] + \
                        detection_box['left'], closest_detection["relative_head_Y"] + \
                        detection_box['top']

                    x1, y1 = closest_detection["x1y1"]
                    if Aimbot.is_target_locked(absolute_head_X, absolute_head_Y):
                        # draw the confidence labels on the bounding boxes
                        cv2.putText(frame, "LOCKED", (x1 + 40, y1),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 244, 113), 2)
                    else:
                        # draw the confidence labels on the bounding boxes
                        cv2.putText(frame, "TARGETING", (x1 + 40, y1),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 113, 244), 2)

                    if Aimbot.is_aimbot_enabled():
                        Aimbot.move_crosshair(
                            self, absolute_head_X, absolute_head_Y)

            if self.collect_data and time.perf_counter() - collect_pause > 1 and Aimbot.is_targeted() and Aimbot.is_aimbot_enabled() and not player_in_frame:  # screenshots can only be taken every 1 second
                cv2.imwrite(f"lib/data/{str(uuid.uuid4())}.jpg", orig_frame)
                collect_pause = time.perf_counter()

            cv2.putText(frame, f"FPS: {int(1/(time.perf_counter() - start_time))}",
                        (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
            # cv2.imshow("Lunar Vision", frame)
            # if cv2.waitKey(1) & 0xFF == ord('0'):
            #     break

    def gen_select_ui(root: tk.Tk, default: Any, label: str, options: List[str], values: List[Any], callback: Callable[[Any], None]):
        frame = tk.Frame(root)
        frame.pack(anchor='w')

        def on_select(option):
            selected_value = option_value_dict[option]
            callback(selected_value)

        # 创建一个StringVar变量，用于设置默认选择
        default_option = tk.StringVar(frame, default)

        # 创建选择框和标签
        label_text = tk.Label(frame, text=label)
        label_text.pack(side=tk.LEFT)

        options = options
        values = values
        option_value_dict = dict(zip(options, values))

        option_menu = tk.OptionMenu(
            frame, default_option, *options, command=on_select)
        option_menu.pack()

        # 设置默认选择为鼠标上侧键
        default_options = [option for option,
                           val in option_value_dict.items() if val == default]

        default_option.set(default_options)

    def gen_slider_ui(root: tk.Tk, default: str, label: str, from_: float, to: float, callback: Callable[[Any], None]):
        # 创建容器1
        frame = tk.Frame(root)
        frame.pack(anchor='w')

        def update(value):
            label_text.config(
                text=f"{label}{value}")
            callback(value)

        # 创建滑块和标签
        label_text = tk.Label(frame, text=label)
        label_text.pack(side=tk.LEFT)  # 将文本标签放在滑块左边
        slider = tk.Scale(frame, from_=from_, to=to, orient=tk.HORIZONTAL,
                          length=300, resolution=0.1, command=update)
        slider.set(default)
        slider.pack(pady=10)

    def clean_up():
        print("\n[INFO] END WAS PRESSED. QUITTING...")
        os._exit(0)


if __name__ == "__main__":
    print("You are in the wrong directory and are running the wrong file; you must run lunar.py")
