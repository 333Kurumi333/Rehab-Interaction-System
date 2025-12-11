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

        self.prev_left = None
        self.prev_right = None
        self.smooth_factor = 0.6  # 0.1(超平滑/延遲大) ~ 1.0(無平滑/反應快)
        
    def _smooth_coordinate(self, prev_pos, curr_pos):
        """ 平滑化數學公式 """
        if prev_pos is None:
            return curr_pos
        # 新位置 = 舊位置 * 40% + 新讀值 * 60%
        new_x = int(prev_pos[0] * (1 - self.smooth_factor) + curr_pos[0] * self.smooth_factor)
        new_y = int(prev_pos[1] * (1 - self.smooth_factor) + curr_pos[1] * self.smooth_factor)
        return (new_x, new_y)

    def process_frame(self, frame):
        """
        輸入原始影像，回傳：
        1. 處理過的影像 (畫上骨架)
        2. 左手手掌的座標 (x, y) 或 None (如果沒偵測到)
        3. 右手手掌的座標 (x, y) 或 None (如果沒偵測到)
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

        left_hand_pos = None  # 左手手掌座標
        right_hand_pos = None # 右手手掌座標

        if results.pose_landmarks: # 如果畫面上有人
            # 隱藏骨架線，不繪製
            # self.mp_drawing.draw_landmarks(
            #     image, #畫布=image
            #     results.pose_landmarks, #畫關節點
            #     self.mp_pose.POSE_CONNECTIONS #畫關節點間的連線
            # )

            # 取得畫面尺寸
            h, w, c = image.shape # 取得畫面尺寸 Height Width Channel(通常是 3，代表 R、G、B)

            # === 提取左手手掌中心座標 ===
            left_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST]
            left_pinky = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_PINKY]
            left_index = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_INDEX]

            # 計算左手手掌中心（手腕、小指、食指的三點平均）
            left_palm_x = (left_wrist.x + left_pinky.x + left_index.x) / 3
            left_palm_y = (left_wrist.y + left_pinky.y + left_index.y) / 3

            current_left = (int(left_palm_x * w), int(left_palm_y * h))

            # 左手平滑處理
            left_hand_pos = self._smooth_coordinate(self.prev_left, current_left)
            self.prev_left = left_hand_pos # 更新記憶

            # 畫出左手觸擊範圍
            # 1. 外圈半透明區域 (觸擊有效範圍)
            overlay = image.copy()
            cv2.circle(overlay, left_hand_pos, 65, (0, 255, 255), -1)  # 黃色半透明外圈
            cv2.addWeighted(overlay, 0.2, image, 0.8, 0, image)  # 20% 透明度

            # 2. 中心點 (黃色實心)
            cv2.circle(image, left_hand_pos, 15, (0, 255, 255), -1)

            # === 提取右手手掌中心座標 ===
            right_wrist = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]
            right_pinky = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_PINKY]
            right_index = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_INDEX]

            # 計算右手手掌中心（手腕、小指、食指的三點平均）
            right_palm_x = (right_wrist.x + right_pinky.x + right_index.x) / 3
            right_palm_y = (right_wrist.y + right_pinky.y + right_index.y) / 3

            current_right = (int(right_palm_x * w), int(right_palm_y * h))

            # 右手平滑處理
            right_hand_pos = self._smooth_coordinate(self.prev_right, current_right)
            self.prev_right = right_hand_pos # 更新記憶

            # 畫出右手觸擊範圍
            # 1. 外圈半透明區域 (觸擊有效範圍)
            overlay = image.copy()
            cv2.circle(overlay, right_hand_pos, 65, (255, 255, 0), -1)  # 青色半透明外圈
            cv2.addWeighted(overlay, 0.2, image, 0.8, 0, image)  # 20% 透明度

            # 2. 中心點 (青色實心)
            cv2.circle(image, right_hand_pos, 15, (255, 255, 0), -1)
    
        else:
            # 重新下次人出現時，不會從舊位置飛過來，而是直接出現在新位置
            self.prev_left = None
            self.prev_right = None

        return image, left_hand_pos, right_hand_pos #回傳圖片和雙手座標