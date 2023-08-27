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
from lib.interception_py.consts import interception_filter_key_state, interception_filter_mouse_state, interception_mouse_flag
from lib.interception_py.interception import interception
from lib.interception_py.stroke import mouse_stroke

# from lib.memory import SharedMemoryWriter

# DETECTION_BOX = 200
# DEFAULT_AIM_WIDTH = 128
# DEFAULT_AIM_HEIGHT = 128

DEFAULT_TARGET_HEAD_RATIO = 3.5
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
    aim_width = setting_config["aim_width"]
    aim_height = setting_config["aim_height"]
    max_pixel = setting_config["max_pixel"]
    # det_box_width = 0
    sensitivity = float(setting_config["sensitivity"])
    det_model_size = int(setting_config["det_model_size"])
    mouse_delay_microsecond = setting_config["mouse_delay_microsecond"]
    absolute_head_X = 0
    absolute_head_Y = 0
    total_length = 0
    max_soomth_length = setting_config["max_soomth_length"]
    aim_mode = setting_config["aim_mode"]
    d_time: float = 0.00

    def __init__(self, box_constant=416, collect_data=False, mouse_delay=0.0001, debug=False):
        # controls the initial centered box width and height of the "Lunar Vision" window
        # controls the size of the detection box (equaling the width and height)
        self.box_constant = box_constant

        print("[INFO] Loading the neural network model")
        self.model = torch.hub.load(
            'lib/yolov5-master', 'custom', path='lib/valorant-02.pt', source='local', force_reload=False)

        # 多个gpu推理
        if torch.cuda.device_count() > 1:
            self.model = torch.nn.DataParallel(self.model)

        if torch.cuda.is_available():
            print(colored("CUDA ACCELERATION [ENABLED]", "green"))
            self.model = self.model.to('cuda')

        else:
            print(colored("[!] CUDA ACCELERATION IS UNAVAILABLE", "red"))
            print(colored(
                "[!] Check your PyTorch installation, else performance will be poor", "red"))

        # base confidence threshold (or base detection (0-1)
        self.model.conf = 0.45
        self.model.iou = 0.45  # NMS IoU (0-1)
        # self.model.max_det = 500
        self.model.amp = True
        # 使用模型的 eval 模式
        # self.model.eval()

        self.collect_data = collect_data
        self.mouse_delay = mouse_delay
        self.debug = debug

        # 自瞄距离
        # self.aim_width, self.aim_height = DEFAULT_AIM_WIDTH, DEFAULT_AIM_HEIGHT

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
        if Aimbot.aimkey == "auto":
            return True
        else:
            return True if win32api.GetKeyState(int(Aimbot.aimkey, 16)) in (-127, -128) else False

    def is_fire():
        return True if win32api.GetKeyState(int("0x01", 16)) in (-127, -128) else False

    def is_target_locked(x, y):
        # plus/minus 5 pixel threshold
        threshold = 2
        return True if 960 - threshold <= x <= 960 + threshold and 540 - threshold <= y <= 540 + threshold else False

    def move_crosshair(self, x, y):
        if Aimbot.is_targeted() == False or Aimbot.is_fire():
            Aimbot.total_length = 0

        if Aimbot.is_targeted() and Aimbot.is_point_inside_rectangle(self, x, y):
            # 灵敏度每减0.1，值加0.2
            scale = 1 + (1 - Aimbot.sensitivity) * 2
        else:

            Aimbot.absolute_head_X = 0
            Aimbot.absolute_head_Y = 0
            return  # TODO

        if Aimbot.is_target_locked(x, y):
            return
        stroke = mouse_stroke(
            0, 0, 0, 0, 0, 200)
        for rel_x, rel_y in Aimbot.interpolate_coordinates_from_center((x, y), scale):
            self.inter.inter.set_filter(
                interception.is_mouse, interception_filter_mouse_state.INTERCEPTION_FILTER_MOUSE_MOVE.value)

            # print(rel_x, rel_y)
            stroke.x = rel_x
            stroke.y = rel_y
            self.inter.inter.send(Inter.mdevice, stroke)
            Aimbot.delayMicrosecond(1)

        # 防抖睡眠
        # time.sleep(Aimbot.mouse_delay_microsecond / 1_000_000_000)
        # generator yields pixel tuples for relative movement

    def interpolate_coordinates_from_center(absolute_coordinates, scale):
        diff_x = (
            absolute_coordinates[0] - Aimbot.half_screen_width) * scale
        diff_y = (
            absolute_coordinates[1] - Aimbot.half_screen_height) * scale

        length = int(math.dist((0, 0), (diff_x, diff_y)))

        # 防止抖动

        # if length <= 5:
        #     return
        # 单次瞄准模式
        if Aimbot.aim_mode == 0 and Aimbot.total_length != 0:
            # print(f"锁定：{Aimbot.total_length}")
            return

        if Aimbot.total_length == length:
            # print(f"锁定：{Aimbot.total_length}")
            return

        Aimbot.total_length = length

        if length == 0:
            return
        # yield int(diff_x / abs(diff_x or 1) * Aimbot.max_pixel), int(diff_y / abs(diff_y or 1) * Aimbot.max_pixel)
        # yield int(diff_x), int(diff_y)

        # 旧方案
        # print(f"diff_x:{diff_x},diff_y:{diff_y},length:{length}")
        # pixel_increment = Aimbot.pixel_increment
        # x = y = sum_x = sum_y = 0
        # unit_x = round(diff_x/length)
        # unit_y = round(diff_y/length)
        # for k in range(0, length):
        #     sum_x += x
        #     sum_y += y
        #     x, y = round(unit_x * k - sum_x), round(unit_y * k - sum_y)
        #     # print(sum_x, sum_y)
        #     yield x, y

        # for k in range(0, length):
        #     yield int(diff_x / abs(diff_x or 1)), int(diff_y / abs(diff_y or 1))
        # 最终方案
        total_step = int(max(abs(diff_x), abs(diff_y)))
        dif = int(total_step - int(min(abs(diff_x), abs(diff_y))))
        dif_array = random.sample(range(total_step), dif)

        if length <= Aimbot.max_soomth_length:
            max_pixel = Aimbot.max_pixel
        else:
            max_pixel = 1

        x = 0
        y = 0
        if int(abs(diff_x)) == 0:
            x = 0
        else:
            x = int(diff_x / abs(diff_x)) * max_pixel

        if int(abs(diff_y)) == 0:
            y = 0
        else:
            y = int(diff_y / abs(diff_y)) * max_pixel

        for k in range(0, round(total_step / max_pixel)):
            if k in dif_array:
                if abs(diff_x) > abs(diff_y):
                    yield x, 0
                if abs(diff_x) < abs(diff_y):
                    yield 0, y
            else:
                yield x, y

        # 新方案
        # 近距离
        # if length <= 30:
        # for k in range(0, length):
        #     x = y = 0
        #     while x == 0 and y == 0:
        #         if diff_x > 0:
        #             x = random.choice([0, 1])
        #             # x = 1
        #         else:
        #             x = random.choice([-1, 0])
        #             # x = -1

        #         if diff_y > 0:
        #             y = random.choice([0, 1])
        #             # y = 1
        #         else:
        #             y = random.choice([-1, 0])
        #             # y = -1

        #     yield x, y
        # 远距离
        # else:
        # abs_diff_x = abs(diff_x)
        # abs_diff_y = abs(diff_y)
        # for k in range(0, Aimbot.total_length):
        #     x = Aimbot.accelerate_decelerate(k, Aimbot.total_length)
        #     y = Aimbot.accelerate_decelerate(k, Aimbot.total_length)

        #     if diff_x > 0:
        #         x = min(x, diff_x)
        #     else:
        #         x = max(-x, diff_x)

        #     if diff_y > 0:
        #         y = min(y, diff_y)
        #     else:
        #         y = max(-y, diff_y)

        #     if x != 0 or y != 0:
        #         yield round(x), round(y)

    # 判断点是否在自瞄范围内
    def is_point_inside_rectangle(self, x0, y0):
        screen_width = Aimbot.half_screen_width * 2
        screen_height = Aimbot.half_screen_height * 2

        rect_left = (screen_width - Aimbot.aim_width) // 2
        rect_right = rect_left + Aimbot.aim_width
        rect_top = (screen_height - Aimbot.aim_height) // 2
        rect_bottom = rect_top + Aimbot.aim_height

        if rect_left <= x0 <= rect_right and rect_top <= y0 <= rect_bottom:
            return True
        else:
            return False

    # 获取加减速值
    def accelerate_decelerate(k, total_steps):
        max_speed = min(Aimbot.max_pixel, total_steps)
        acceleration_phase = total_steps // 2
        deceleration_phase = total_steps - acceleration_phase

        if k < acceleration_phase:
            speed = (k + 1) * max_speed // acceleration_phase
        else:
            deceleration_steps = k - acceleration_phase
            speed = ((deceleration_phase - deceleration_steps) *
                     max_speed // deceleration_phase)

        return speed

    def start(self):
        print("[INFO] Beginning screen capture")
        Aimbot.update_status_aimbot()

        detection_box = {'left': int(Aimbot.half_screen_width - self.box_constant//2),  # x1 coord (for top-left corner of the box)
                         # y1 coord (for top-left corner of the box)
                         'top': int(Aimbot.half_screen_height - self.box_constant//2),
                         'width': int(self.box_constant),  # width of the box
                         'height': int(self.box_constant)}  # height of the box

        # 定时修改瞄准比值（伪随机决定瞄准位置）
        target_ratio_y = DEFAULT_TARGET_BODY_RATIO
        DEFAULT_TARGET_X = 2
        target_ratio_x = DEFAULT_TARGET_X

        def update_target_ratio():
            nonlocal target_ratio_y
            nonlocal target_ratio_x
            while True:
                # target_ratio_y -= 0.1
                if Aimbot.aimtarget == 0:
                    # if target_ratio_y <= 2.2:
                    target_ratio_y = DEFAULT_TARGET_HEAD_RATIO
                elif Aimbot.aimtarget == 1:
                    # if target_ratio_y <= 2.2:
                    target_ratio_y = random.choice(
                        [DEFAULT_TARGET_BODY_RATIO, DEFAULT_TARGET_HEAD_RATIO])
                elif Aimbot.aimtarget == 2:
                    # if target_ratio_y <= 3.0:
                    target_ratio_y = DEFAULT_TARGET_BODY_RATIO

                time.sleep(4)

        thread_1 = threading.Thread(target=update_target_ratio)
        thread_1.daemon = True
        thread_1.start()

        def update_config_ui():

            # 创建主窗口
            root = tk.Tk()
            root.title("参数设置")

            def update_sensitivity(value):
                Aimbot.sensitivity = float(value)
                Aimbot.setting_config['sensitivity'] = float(value)
                with open(config_file, 'w') as file:
                    json.dump(Aimbot.setting_config, file, indent=4)

            Aimbot.gen_slider_ui(root=root, default=Aimbot.sensitivity,
                                 label="设置sensitivity（游戏内鼠标的灵敏度）：", from_=0.1, to=1, resolution=0.1, callback=update_sensitivity)

            # def update_max_pixel(value):
            #     Aimbot.max_pixel = int(value)
            #     Aimbot.setting_config['max_pixel'] = int(value)
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.max_pixel,
            #                      label="设置max_pixel：", from_=1, to=10, resolution=1, callback=update_max_pixel)

            # def update_mouse_delay_microsecond(value):
            #     Aimbot.mouse_delay_microsecond = float(value)
            #     Aimbot.setting_config['mouse_delay_microsecond'] = float(value)
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.mouse_delay_microsecond,
            #                      label="设置mouse_delay_microsecond：", from_=0.1, to=10, resolution=0.1, callback=update_mouse_delay_microsecond)

            # def update_det_model_size(value):
            #     Aimbot.det_model_size = int(value)
            #     Aimbot.setting_config['det_model_size'] = int(value)
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.det_model_size,
            #                      label="设置det_model_size：", from_=200, to=416, resolution=1, callback=update_det_model_size)

            # def update_aim_width(value):
            #     Aimbot.aim_width = int(value)
            #     Aimbot.setting_config['aim_width'] = int(value)
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.aim_width,
            #                      label="设置aim_width：", from_=2, to=512, resolution=1, callback=update_aim_width)

            # def update_aim_height(value):
            #     Aimbot.aim_height = int(value)
            #     Aimbot.setting_config['aim_height'] = int(value)
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.aim_height,
            #                      label="设置aim_height：", from_=2, to=512, resolution=1, callback=update_aim_height)

            def update_aim_content(value):
                Aimbot.aim_width = int(value)
                Aimbot.aim_height = int(value)
                Aimbot.setting_config['aim_width'] = int(value)
                Aimbot.setting_config['aim_height'] = int(value)
                with open(config_file, 'w') as file:
                    json.dump(Aimbot.setting_config, file, indent=4)

            Aimbot.gen_slider_ui(root=root, default=Aimbot.aim_width,
                                 label="设置自瞄范围：", from_=2, to=512, resolution=1, callback=update_aim_content)

            # def update_max_soomth_length(value):
            #     Aimbot.max_soomth_length = int(value)
            #     Aimbot.setting_config['max_soomth_length'] = int(value)
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_slider_ui(root=root, default=Aimbot.max_soomth_length,
            #                      label="设置max_soomth_length：", from_=5, to=100, resolution=1, callback=update_max_soomth_length)

            def aim_key_on_select(selected_value):
                Aimbot.aimkey = selected_value
                Aimbot.setting_config["aimkey"] = selected_value
                with open(config_file, 'w') as file:
                    json.dump(Aimbot.setting_config, file, indent=4)

            Aimbot.gen_select_ui(root=root, default=Aimbot.aimkey, label="选择自瞄按键：", options=[
                                 "Ctrl", "Shift", "鼠标上侧键", "鼠标下侧键", "鼠标左键", "鼠标右键", "Alt", "空格键"], values=["0x11", "0x10", "0x06", "0x05", "0x01", "0x02", "0xa4", "0x20"], callback=aim_key_on_select)

            def aim_mode_on_select(selected_value):
                Aimbot.aim_mode = selected_value
                Aimbot.setting_config["aim_mode"] = selected_value
                with open(config_file, 'w') as file:
                    json.dump(Aimbot.setting_config, file, indent=4)

            Aimbot.gen_select_ui(root=root, default=Aimbot.aim_mode, label="选择自瞄模式：", options=[
                                 "单次瞄准（推荐）", "跟随瞄准"], values=[0, 1], callback=aim_mode_on_select)

            # def aim_target_on_select(selected_value):
            #     Aimbot.aimtarget = selected_value
            #     Aimbot.setting_config["aimtarget"] = selected_value
            #     with open(config_file, 'w') as file:
            #         json.dump(Aimbot.setting_config, file, indent=4)

            # Aimbot.gen_select_ui(root=root, default=Aimbot.aimtarget, label="选择自瞄位置：", options=[
            #                      "头部（危险）", "随机头部身体", "身体"], values=[0, 1, 2], callback=aim_target_on_select)

            # 运行主循环
            root.mainloop()

        thread_2 = threading.Thread(target=update_config_ui)
        thread_2.daemon = True
        thread_2.start()

        # def aim_thread():
        #     while True:
        #         if Aimbot.is_aimbot_enabled():
        #             Aimbot.move_crosshair(
        #                 self, Aimbot.absolute_head_X, Aimbot.absolute_head_Y)
        #         time.sleep(0.000000001)

        # thread_3 = threading.Thread(target=aim_thread)
        # thread_3.daemon = True
        # thread_3.start()

        while True:
            start_time = time.perf_counter()
            frame = np.array(Aimbot.screen.grab(detection_box))
            # 使用torch.no_grad()
            # with torch.no_grad():
            results = self.model(frame, size=Aimbot.det_model_size)

            if len(results.xyxy[0]) != 0:  # player detected
                least_crosshair_dist = closest_detection = player_in_frame = False
                # iterate over each player detected
                for *box, conf, cls in results.xyxy[0]:
                    x1y1 = [int(x.item()) for x in box[:2]]
                    x2y2 = [int(x.item()) for x in box[2:]]
                    x1, y1, x2, y2, conf = *x1y1, *x2y2, conf.item()
                    height = y2 - y1
                    # offset to roughly approximate the head using a ratio of the height
                    # - height/target_ratio_y

                    relative_head_X, relative_head_Y = int(
                        (x1 + x2)/target_ratio_x), int((y1 + y2)/2)
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

                    # self.det_box_width = (closest_detection["x2y2"][0] -
                    #                       closest_detection["x1y1"][0])

                    x1 = int((detection_box["width"] - Aimbot.aim_width) // 2)
                    y1 = int(
                        (detection_box['height'] - Aimbot.aim_height) // 2)
                    x2 = int(x1 + Aimbot.aim_width)
                    y2 = int(y1 + Aimbot.aim_height)

                    # print(x1, x2, y1, y2)
                    # 在背景图像上绘制矩形
                    cv2.rectangle(frame, (x1, y1), (x2, y2),
                                  (115, 113, 244), 2)

                    cv2.circle(
                        frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), 5, (115, 244, 113), -1)
                    # draw line from the crosshair to the head
                    cv2.line(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), (
                        self.box_constant//2, self.box_constant//2), (244, 242, 113), 2)

                    absolute_head_X, absolute_head_Y = (closest_detection["relative_head_X"] +
                                                        detection_box['left'], closest_detection["relative_head_Y"] +
                                                        detection_box['top'])

                    x1, y1 = closest_detection["x1y1"]
                    if Aimbot.is_target_locked(absolute_head_X, absolute_head_Y):
                        # draw the confidence labels on the bounding boxes
                        cv2.putText(frame, "LOCKED", (x1 + 40, y1),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 244, 113), 2)
                    else:
                        # draw the confidence labels on the bounding boxes
                        cv2.putText(frame, "TARGETING", (x1 + 40, y1),
                                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 113, 244), 2)

                    Aimbot.absolute_head_X = absolute_head_X
                    Aimbot.absolute_head_Y = absolute_head_Y
                    if Aimbot.is_aimbot_enabled():
                        Aimbot.move_crosshair(
                            self, absolute_head_X, absolute_head_Y)

            cv2.putText(frame, f"FPS: {int(1/(time.perf_counter() - start_time))}",
                        (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
            cv2.imshow("Lunar Vision", frame)
            if cv2.waitKey(1) & 0xFF == ord('0'):
                break
            # 释放 GPU 内存
            torch.cuda.empty_cache()

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

    def gen_slider_ui(root: tk.Tk, default: str, label: str, from_: float, to: float, resolution: float, callback: Callable[[Any], None]):

        # 创建容器1
        frame = tk.Frame(root)
        frame.pack(anchor='w')

        def update(value):
            label_text.config(
                text=f"{label}{value}")
            callback(value)

        # 创建滑块和标签
        label_text = tk.Label(frame, text=label)
        label_text.config(text=f"{label}{default}")
        label_text.pack(side=tk.LEFT)  # 将文本标签放在滑块左边
        slider = tk.Scale(frame, from_=from_, to=to, orient=tk.HORIZONTAL,
                          length=300, resolution=resolution, command=update)
        slider.set(default)
        slider.pack(pady=10)

    def delayMicrosecond(t):    # 微秒级延时函数
        start, end = 0, 0           # 声明变量
        start = time.time()       # 记录开始时间
        t = t/1_000_000_000_000_000    # 将输入t的单位转换为秒，-3是时间补偿
        while end-start < t:  # 循环至时间差值大于或等于设定值时
            end = time.time()     # 记录结束时间

    def clean_up():
        print("\n[INFO] END WAS PRESSED. QUITTING...")
        os._exit(0)


if __name__ == "__main__":
    print("You are in the wrong directory and are running the wrong file; you must run lunar.py")
