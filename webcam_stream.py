import cv2
import time
import threading


class WebcamStream:
    """Webcam 多執行緒串流 - 在背景持續讀取攝影機畫面"""
    
    def __init__(self, src=0, width=1920, height=1080):
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False
        
        # 計時與追蹤
        self.frame_id = 0            # 幀 ID
        self.last_read_time = 0      # 上次讀取耗時 (ms)
        self.read_count = 0          # 已讀取幀數
        self.total_read_time = 0     # 總讀取時間
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            
            start_time = time.time()
            (grabbed, frame) = self.stream.read()
            elapsed = (time.time() - start_time) * 1000
            
            with self.lock:
                self.grabbed = grabbed
                self.frame = frame
                self.frame_id += 1
                self.last_read_time = elapsed
                self.read_count += 1
                self.total_read_time += elapsed

    def read(self):
        with self.lock:
            return self.grabbed, self.frame
    
    def read_with_stats(self):
        """回傳畫面及統計資訊"""
        with self.lock:
            return self.grabbed, self.frame, self.frame_id, self.last_read_time
    
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
        self.stream.release()

