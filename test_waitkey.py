"""
測試完整遊戲環境下的 waitKey 延遲
"""
import cv2
import time
import numpy as np
import threading
import sys
sys.path.append('.')

from camera_sensor import PoseDetector
# 從 main.py 複製 WebcamStream 和 VideoPlayerThread

class WebcamStream:
    def __init__(self, src=0, width=1920, height=1080):
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if self.stream.isOpened():
                self.grabbed, self.frame = self.stream.read()
            time.sleep(0.001)

    def read(self):
        return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()


def test_game_like():
    print("=" * 50)
    print("測試類似遊戲的環境")
    print("=" * 50)
    
    # 1. 啟動 WebcamStream
    print("啟動 WebcamStream...")
    cap = WebcamStream(src=0, width=1920, height=1080).start()
    time.sleep(1)
    
    # 2. 啟動 PoseDetector
    print("啟動 PoseDetector...")
    sensor = PoseDetector()
    sensor.start()
    time.sleep(2)  # 讓 YOLO 暖機
    
    cv2.namedWindow("Test", cv2.WINDOW_NORMAL)
    
    print("\n開始測試...")
    waitkey_times = []
    imshow_times = []
    pose_times = []
    
    for i in range(100):
        t0 = time.time()
        
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        
        # Pose 處理
        t1 = time.time()
        processed_image, left_pos, right_pos = sensor.process_frame(frame)
        t2 = time.time()
        
        # imshow
        t3 = time.time()
        cv2.imshow("Test", processed_image)
        t4 = time.time()
        
        # waitKey
        cv2.waitKey(1)
        t5 = time.time()
        
        pose_times.append((t2 - t1) * 1000)
        imshow_times.append((t4 - t3) * 1000)
        waitkey_times.append((t5 - t4) * 1000)
    
    print(f"\nPose 平均: {sum(pose_times)/len(pose_times):.2f}ms")
    print(f"imshow 平均: {sum(imshow_times)/len(imshow_times):.2f}ms")
    print(f"waitKey 平均: {sum(waitkey_times)/len(waitkey_times):.2f}ms")
    
    sensor.stop()
    cap.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_game_like()
    print("\n測試完成！")
