import cv2
import time
import threading


class VideoPlayerThread:
    """背景影片多執行緒播放器 - 在背景持續讀取影片幀"""
    
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0 or self.fps > 120:
            self.fps = 30
        self.frame_duration = 1.0 / self.fps
        
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
        self.frame_available = True
        if not self.grabbed:
            print(f"無法讀取背景影片: {video_path}")
            self.frame_available = False

    def start(self):
        if self.frame_available:
            threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            start_time = time.time()
            grabbed, frame = self.cap.read()
            if not grabbed:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            self.grabbed, self.frame = grabbed, frame
            elapsed = time.time() - start_time
            wait_time = self.frame_duration - elapsed
            if wait_time > 0:
                time.sleep(wait_time)

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()
