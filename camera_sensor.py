import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        # 初始化 MediaPipe
        self.mp_drawing = mp.solutions.drawing_utils #畫圖工具
        self.mp_pose = mp.solutions.pose #人體模型藍圖
        self.pose = self.mp_pose.Pose(
            model_complexity=0,
            min_detection_confidence=0.5, #AI辨識人的靈敏度
            min_tracking_confidence=0.5 #AI追蹤人的靈敏度
        )

        self.prev_left = None
        self.prev_right = None
        self.smooth_factor = 0.7  # 0.1(超平滑/延遲大) ~ 1.0(無平滑/反應快)
        
    def _smooth_coordinate(self, prev_pos, curr_pos):
        """ 平滑化數學公式 """
        if prev_pos is None:
            return curr_pos
        # 新位置 = 舊位置 * 40% + 新讀值 * 60%
        new_x = int(prev_pos[0] * (1 - self.smooth_factor) + curr_pos[0] * self.smooth_factor)
        new_y = int(prev_pos[1] * (1 - self.smooth_factor) + curr_pos[1] * self.smooth_factor)
        return (new_x, new_y)

    def _process_hand(self, results, w, h, pinky_landmark, index_landmark, prev_pos):
        """處理單隻手的偵測與平滑化"""
        pinky = results.pose_landmarks.landmark[pinky_landmark]
        index = results.pose_landmarks.landmark[index_landmark]
        palm_x = (pinky.x + index.x) / 2
        palm_y = (pinky.y + index.y) / 2
        current = (int(palm_x * w), int(palm_y * h))
        return self._smooth_coordinate(prev_pos, current)

    def _draw_hand_circle(self, image, pos, color):
        """繪製手部觸擊範圍"""
        overlay = image.copy()
        cv2.circle(overlay, pos, 65, color, -1)
        cv2.addWeighted(overlay, 0.2, image, 0.8, 0, image)
        cv2.circle(image, pos, 15, color, -1)

    def process_frame(self, frame):
        """
        輸入原始影像，回傳：
        1. 處理過的影像 (畫上骨架)
        2. 左手手掌的座標 (x, y) 或 None (如果沒偵測到)
        3. 右手手掌的座標 (x, y) 或 None (如果沒偵測到)
        """
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self.pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        left_hand_pos = None
        right_hand_pos = None

        if results.pose_landmarks:
            h, w, c = image.shape

            # 左手處理
            left_hand_pos = self._process_hand(
                results, w, h,
                self.mp_pose.PoseLandmark.LEFT_PINKY,
                self.mp_pose.PoseLandmark.LEFT_INDEX,
                self.prev_left
            )
            self.prev_left = left_hand_pos
            self._draw_hand_circle(image, left_hand_pos, (0, 255, 255))

            # 右手處理
            right_hand_pos = self._process_hand(
                results, w, h,
                self.mp_pose.PoseLandmark.RIGHT_PINKY,
                self.mp_pose.PoseLandmark.RIGHT_INDEX,
                self.prev_right
            )
            self.prev_right = right_hand_pos
            self._draw_hand_circle(image, right_hand_pos, (255, 255, 0))
        else:
            self.prev_left = None
            self.prev_right = None

        return image, left_hand_pos, right_hand_pos


class PoseDetectorThread:
    """姿態偵測執行緒包裝器 - 在背景執行姿態偵測以提升 FPS"""
    
    def __init__(self):
        import threading
        self.detector = PoseDetector()
        self.frame = None
        self.processed_image = None
        self.left_hand_pos = None
        self.right_hand_pos = None
        self.stopped = False
        self.lock = threading.Lock()
        self.new_frame_event = threading.Event()
    
    def start(self):
        import threading
        threading.Thread(target=self._update, args=(), daemon=True).start()
        return self
    
    def _update(self):
        """背景執行緒：持續處理最新的畫面"""
        while not self.stopped:
            # 等待新畫面
            self.new_frame_event.wait(timeout=0.1)
            self.new_frame_event.clear()
            
            with self.lock:
                frame = self.frame
            
            if frame is not None:
                # 執行姿態偵測 (耗時操作)
                processed, left, right = self.detector.process_frame(frame)
                
                with self.lock:
                    self.processed_image = processed
                    self.left_hand_pos = left
                    self.right_hand_pos = right
    
    def submit_frame(self, frame):
        """主執行緒：提交新畫面給背景處理"""
        with self.lock:
            self.frame = frame
        self.new_frame_event.set()
    
    def get_result(self):
        """主執行緒：取得最新處理結果 (不阻塞)"""
        with self.lock:
            return self.processed_image, self.left_hand_pos, self.right_hand_pos
    
    def stop(self):
        self.stopped = True