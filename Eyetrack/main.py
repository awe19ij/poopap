import cv2
import numpy as np
import csv
import time
import threading
import requests
from .gaze_tracking import GazeTracking
from django.conf import settings
import os

class GazeTrackingSession:
    def __init__(self, video_url=None, status="initialized"):
        self.sections = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
            "E": 0,
            "F": 0
        }
        self.section = "None"
        self.thread = None
        self.running = False
        self.video_url = video_url  # video_url 속성을 초기화
        self.status = status

    def Section(self, where):
        if where in self.sections:
            self.sections[where] += 1
            return self.sections[where]

    def Thread_run(self):
        if not self.running:
            return
        print(self.section, ":", self.Section(self.section))
        self.thread = threading.Timer(0.1, self.Thread_run)
        self.thread.daemon = True
        self.thread.start()

    def start_eye_tracking(self, video_path):
        if video_path is None:
            raise ValueError("Video path must not be None")
        
        self.running = True
        self.video_path = video_path
        self.thread = self.Thread_run()

        avg_left_hor_gaze = 0
        avg_right_hor_gaze = 0
        avg_top_ver_gaze = 0
        avg_bottom_ver_gaze = 0

        total_left_hor_gaze = 0
        total_right_hor_gaze = 0
        total_top_ver_gaze = 0
        total_bottom_ver_gaze = 0

        webcam = cv2.VideoCapture(video_path)
        if not webcam.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")

        test_count = 1
        flag = 0
        gaze = GazeTracking()

        frame_rate = int(webcam.get(cv2.CAP_PROP_FPS))
        max_frames = frame_rate * 180  # 180초 = 3분

        frame_count = 0
        while self.running and frame_count < max_frames:
            _, frame = webcam.read()
            if frame is None:
                break

            frame_count += 1
            gaze.refresh(frame)
            frame, loc1, loc2 = gaze.annotated_frame()

            if test_count < 50:
                if gaze.horizontal_ratio() is not None and gaze.vertical_ratio() is not None:
                    total_left_hor_gaze += gaze.horizontal_ratio()
                    total_top_ver_gaze += gaze.vertical_ratio()
                    test_count += 1
            elif 50 <= test_count < 100:
                if gaze.horizontal_ratio() is not None and gaze.vertical_ratio() is not None:
                    total_right_hor_gaze += gaze.horizontal_ratio()
                    total_top_ver_gaze += gaze.vertical_ratio()
                    test_count += 1
            elif 100 <= test_count < 150:
                if gaze.horizontal_ratio() is not None and gaze.vertical_ratio() is not None:
                    total_left_hor_gaze += gaze.horizontal_ratio()
                    total_bottom_ver_gaze += gaze.vertical_ratio()
                    test_count += 1
            elif 150 <= test_count < 200:
                if gaze.horizontal_ratio() is not None and gaze.vertical_ratio() is not None:
                    total_right_hor_gaze += gaze.horizontal_ratio()
                    total_bottom_ver_gaze += gaze.vertical_ratio()
                    test_count += 1
            else:
                if flag == 0:
                    avg_left_hor_gaze = total_left_hor_gaze / 100
                    avg_right_hor_gaze = total_right_hor_gaze / 100
                    avg_top_ver_gaze = total_top_ver_gaze / 100
                    avg_bottom_ver_gaze = total_bottom_ver_gaze / 100
                    flag = 1

                if gaze.is_blinking():
                    text = "Blinking"

                if gaze.is_top_left(avg_left_hor_gaze, avg_top_ver_gaze):
                    text = "Looking top left"
                    self.section = "A"
                elif gaze.is_top_center(avg_top_ver_gaze, avg_right_hor_gaze, avg_left_hor_gaze):
                    text = "Looking top center"
                    self.section = "B"
                elif gaze.is_top_right(avg_right_hor_gaze, avg_top_ver_gaze):
                    text = "Looking top right"
                    self.section = "C"
                elif gaze.is_bottom_left(avg_left_hor_gaze, avg_top_ver_gaze):
                    text = "Looking bottom left"
                    self.section = "D"
                elif gaze.is_bottom_center(avg_top_ver_gaze, avg_right_hor_gaze, avg_left_hor_gaze):
                    text = "Looking bottom center"
                    self.section = "E"
                elif gaze.is_bottom_right(avg_right_hor_gaze, avg_top_ver_gaze):
                    text = "Looking bottom right"
                    self.section = "F"
                gaze_time = int(time.time())
                save_loc1 = loc1
                save_loc2 = loc2
        webcam.release()
        cv2.destroyAllWindows()

    def stop_eye_tracking(self):
        self.running = False
        if self.thread is not None:
            self.thread.cancel()

        csv_filename = os.path.join(settings.BASE_DIR, "Eyetrack/0518/gaze_sections.csv")

        # CSV 파일 헤더
        csv_header = ["Section", "Count"]

        # CSV 파일 쓰기 모드로 열기
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)

            # 헤더 쓰기
            writer.writerow(csv_header)

            # 각 섹션의 횟수를 CSV 파일에 기록
            for section_name, count in self.sections.items():
                writer.writerow([section_name, count])

        print("Data saved to", csv_filename)
        return csv_filename