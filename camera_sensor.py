import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        # 初始化 MediaPipe
        self.mp_drawing = mp.solutions.drawing_utils #畫圖工具
        self.mp_pose = mp.solutions.pose #人體模型藍圖
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, #AI辨識人的靈敏度
            min_tracking_confidence=0.5 #AI追蹤人的靈敏度
        )

    def process_frame(self, frame):
        """
        輸入原始影像，回傳：
        1. 處理過的影像 (畫上骨架)
        2. 手腕的座標 (x, y) 或 None (如果沒偵測到)
        """
        # 翻轉影像與色彩轉換
        frame = cv2.flip(frame, 1) # 翻轉： 讓畫面像照鏡子，方便玩遊戲。
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # 變色： 把顏色調成 AI 看得懂的 RGB 格式。
        image.flags.writeable = False # 鎖定： 告訴 AI 這張圖是唯讀的，加快處理速度。
        
        # 進行偵測
        results = self.pose.process(image) #AI 分析 (process) 拿到數據報告。
        
        # 轉回 BGR 供 OpenCV 顯示
        image.flags.writeable = True #解鎖圖片 (writeable=True) 準備讓畫筆畫圖。
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) #轉回原色 (cvtColor) 讓畫面顯示正常顏色。
        
        wrist_pos = None #歸零座標 (wrist_pos=None) 準備接收新的位置數據。

        if results.pose_landmarks: # 如果畫面上有人
            # 畫出骨架
            self.mp_drawing.draw_landmarks(
                image, #畫布=image
                results.pose_landmarks, #畫關節點
                self.mp_pose.POSE_CONNECTIONS #畫關節點間的連線
            )
            
            # 取得畫面尺寸
            h, w, c = image.shape # 取得畫面尺寸 Height Width Channel(通常是 3，代表 R、G、B)
            
            # 提取右手手腕座標 (Index 16)
            landmark = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST] #results.pose_landmarks.landmark是一個清單，裡面存了 33 個身體部位的資料。self.mp_pose.PoseLandmark.RIGHT_WRIST==16 整句意思： 「請去那 33 個點的清單裡，把第 16 號（右手手腕）的資料拿出來給我。」
            cx, cy = int(landmark.x * w), int(landmark.y * h) #landmark.x 和 landmark.y 都是 0.0 到 1.0 之間的小數, 乘上螢幕長寬才能得到正確座標
            wrist_pos = (cx, cy) 
            
            # 畫出手腕點 (黃色)
            cv2.circle(image, (cx, cy), 15, (0, 255, 255), -1) #在畫面上蓋一個黃色圓點，標記出手腕的位置。image (畫在哪？)(cx, cy) (畫在哪個點？)15 (畫多大？)(0, 255, 255) (畫什麼顏色？)-1 (空心還是實心？)
            
        return image, wrist_pos #回傳圖片和座標