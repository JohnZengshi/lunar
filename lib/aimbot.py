import ctypes
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

from termcolor import colored


class Aimbot:
    extra = ctypes.c_ulong(0)
    screen = mss.mss()
    pixel_increment = 1  # controls how many pixels the mouse moves for each relative movement
    with open("lib/config/config.json") as f:
        sens_config = json.load(f)
    aimbot_status = colored("ENABLED", 'green')

    def __init__(self, box_constant=416, collect_data=False, mouse_delay=0.0001, debug=False):
        # controls the initial centered box width and height of the "Lunar Vision" window
        # controls the size of the detection box (equaling the width and height)
        self.box_constant = box_constant

        print("[INFO] Loading the neural network model")
        self.model = torch.hub.load(
            'lib/yolov5-master', 'custom', path='lib/best.pt', source='local', force_reload=True)
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
        return True if win32api.GetKeyState(0x02) in (-127, -128) else False

    def is_target_locked(x, y):
        # plus/minus 5 pixel threshold
        threshold = 5
        return True if 960 - threshold <= x <= 960 + threshold and 540 - threshold <= y <= 540 + threshold else False

    def start(self):
        print("[INFO] Beginning screen capture")
        Aimbot.update_status_aimbot()
        half_screen_width = ctypes.windll.user32.GetSystemMetrics(
            0)/2  # this should always be 960
        half_screen_height = ctypes.windll.user32.GetSystemMetrics(
            1)/2  # this should always be 540
        detection_box = {'left': int(half_screen_width - self.box_constant//2),  # x1 coord (for top-left corner of the box)
                         # y1 coord (for top-left corner of the box)
                         'top': int(half_screen_height - self.box_constant//2),
                         'width': int(self.box_constant),  # width of the box
                         'height': int(self.box_constant)}  # height of the box
        if self.collect_data:
            collect_pause = 0

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
                        (x1 + x2)/2), int((y1 + y2)/2 - height/2.7)
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
                        # draw the confidence labels on the bounding boxes
                        cv2.putText(frame, f"{int(conf * 100)}%", x1y1,
                                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (244, 113, 116), 2)
                    else:
                        own_player = False
                        if not player_in_frame:
                            player_in_frame = True

                if closest_detection:  # if valid detection exists
                    # draw circle on the head
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
                        print(absolute_head_X, absolute_head_Y)
                        # TODO 共享数据

            if self.collect_data and time.perf_counter() - collect_pause > 1 and Aimbot.is_targeted() and Aimbot.is_aimbot_enabled() and not player_in_frame:  # screenshots can only be taken every 1 second
                cv2.imwrite(f"lib/data/{str(uuid.uuid4())}.jpg", orig_frame)
                collect_pause = time.perf_counter()

            cv2.putText(frame, f"FPS: {int(1/(time.perf_counter() - start_time))}",
                        (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
            cv2.imshow("Lunar Vision", frame)
            if cv2.waitKey(1) & 0xFF == ord('0'):
                break

    def clean_up():
        print("\n[INFO] F2 WAS PRESSED. QUITTING...")
        os._exit(0)


if __name__ == "__main__":
    print("You are in the wrong directory and are running the wrong file; you must run lunar.py")
