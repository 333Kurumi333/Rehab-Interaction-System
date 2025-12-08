import cv2
# 匯入另外三個檔案的 Class
from camera_sensor import PoseDetector
from new_game_logic import GameEngine
from ui_renderer import GameUI

def main():
    # 1. 啟動各個模組
    sensor = PoseDetector()  # 視覺模組

    # 開啟攝影機以取得解析度
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        print("無法開啟攝影機")
        return

    # 取得攝影機解析度
    height, width = frame.shape[:2]

    # 初始化遊戲邏輯（需要畫面尺寸）
    # arc_radius: 半圓大小, zone_count: 區塊數量, note_speed: 物件速度
    logic = GameEngine(
        width=width,
        height=height,
        arc_radius=550,      # 增加半圓半徑 (450 -> 550)
        zone_count=8,        # 增加區塊數量 (原本 4)
        note_speed=8         # 大幅加快速度 (5 -> 8)
    )
    ui = GameUI()  # 介面模組

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # A. 視覺處理：取得影像與雙手手掌座標
        processed_image, left_hand_pos, right_hand_pos = sensor.process_frame(frame)

        # B. 邏輯處理：更新遊戲狀態（物件生成、移動、碰撞判定）
        # 傳入雙手座標，遊戲邏輯會檢查兩隻手
        logic.update_game_state(left_hand_pos, spawn_rate=30)  # 降低 spawn_rate 增加出現頻率 (60 -> 30)
        logic.update_game_state(right_hand_pos, spawn_rate=30)

        # C. 介面處理：把結果畫在畫面上
        # 取得遊戲資料
        notes_data = logic.get_notes_for_drawing()
        arc_info = logic.get_arc_info()
        score = logic.get_score()

        # 繪製遊戲元素
        ui.draw_game_elements(
            processed_image,
            arc_info,
            notes_data,
            score
        )

        # D. 顯示最終畫面
        cv2.imshow('Rehab System - Rhythm Game', processed_image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()