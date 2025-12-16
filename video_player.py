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
        
        # 計時與追蹤
        self.frame_id = 0
        self.last_read_time = 0
        self.read_count = 0
        self.total_read_time = 0
        self.lock = threading.Lock()

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
            
            read_elapsed = (time.time() - start_time) * 1000
            
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame
                self.frame_id += 1
                self.last_read_time = read_elapsed
                self.read_count += 1
                self.total_read_time += read_elapsed
            
            # 控制播放速度
            elapsed = time.time() - start_time
            wait_time = self.frame_duration - elapsed
            if wait_time > 0:
                time.sleep(wait_time)

    def read(self):
        with self.lock:
            return self.frame
    
    def read_with_stats(self):
        """回傳畫面及統計資訊"""
        with self.lock:
            return self.frame, self.frame_id, self.last_read_time
    
    def get_stats(self):
        """取得讀取統計"""
        with self.lock:
            avg = self.total_read_time / self.read_count if self.read_count > 0 else 0
            return {
                'read_count': self.read_count,
                'avg_time_ms': avg,
                'last_time_ms': self.last_read_time
            }

    def stop(self):
        self.stopped = True
        self.cap.release()
