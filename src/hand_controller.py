import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import numpy as np
from threading import Thread


    
class HandController:
    def __init__(self):
        MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        model_content = urllib.request.urlopen(MODEL_URL).read()
        base_options = python.BaseOptions(model_asset_buffer=model_content)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            min_hand_detection_confidence=0.4,
            num_hands=1
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.direction = None
        self.running = False
        self.thread = None


    def start(self):
        self.running = True
        self.thread = Thread(target=self.run_cycle)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def update_direction(self, p0, p1):
        if p0[0] is None and p1[0] is None:
            self.direction = None
            return None
        dx, dy = np.array(p1) - np.array(p0)
        if np.abs(dy) < dx:
            self.direction = 'right'
        if np.abs(dy) < -dx:
            self.direction = 'left'
        # Ось y направлена вниз
        if dy > np.abs(dx):
            self.direction = 'down'
        if dy < -np.abs(dx):
            self.direction = 'up'

    def run_cycle(self):
        cap = cv2.VideoCapture(0)

        while self.running and cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            # Конвертация в формат MediaPipe
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # Детекция
            result = self.detector.detect(mp_image)

            if result.hand_landmarks:
                for hand_id, hand_landmarks in enumerate(result.hand_landmarks):
                    p0 = [None, None]
                    p1 = [None, None]
                    for landmark_id, landmark in enumerate(hand_landmarks):
                        normalized_x = landmark.x
                        normalized_y = landmark.y
                        
                        if landmark_id in [5, 6, 7, 8]:
                                # Конвертация в пиксели
                            height, width = frame.shape[:2]
                            pixel_x = int(normalized_x * width)
                            pixel_y = int(normalized_y * height)
                            if landmark_id == 5:
                                p0[0] = pixel_x
                                p0[1] = pixel_y
                            if landmark_id == 8:
                                p1[0] = pixel_x
                                p1[1] = pixel_y
                            cv2.circle(frame, (pixel_x, pixel_y), 5, (0,255,0), -1)
                    self.update_direction(p0, p1)
                    if p0[0] is not None and p1[0] is not None:
                        cv2.arrowedLine(frame, p0, p1, (0, 0, 255), 2) 
                        cv2.putText(frame, self.direction, (300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)

            cv2.imshow('Hand Controller', frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                self.running = False
                break
        
        cap.release()
        cv2.destroyAllWindows()