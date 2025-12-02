import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        # 初始化 MediaPipe
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )

    def process_frame(self, frame):
        """
        輸入原始影像，回傳：
        1. 處理過的影像 (畫上骨架)
        2. 手腕的座標 (x, y) 或 None (如果沒偵測到)
        """
        # 翻轉影像與色彩轉換
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        
        # 進行偵測
        results = self.pose.process(image)
        
        # 轉回 BGR 供 OpenCV 顯示
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        wrist_pos = None

        if results.pose_landmarks:
            # 畫出骨架
            self.mp_drawing.draw_landmarks(
                image, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )
            
            # 取得畫面尺寸
            h, w, c = image.shape
            
            # 提取右手手腕座標 (Index 16)
            landmark = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            wrist_pos = (cx, cy)
            
            # 畫出手腕點 (黃色)
            cv2.circle(image, (cx, cy), 15, (0, 255, 255), -1)
            
        return image, wrist_pos