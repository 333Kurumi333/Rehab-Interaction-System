import cv2
# 匯入另外三個檔案的 Class
from camera_sensor import PoseDetector
from game_logic import GameEngine
from ui_renderer import GameUI

def main():
    # 1. 啟動各個模組
    sensor = PoseDetector()  # 視覺模組
    logic = GameEngine()     # 邏輯模組
    ui = GameUI()            # 介面模組

    # 開啟攝影機
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # A. 視覺處理：取得影像與手腕座標
        processed_image, wrist_pos = sensor.process_frame(frame)

        # B. 邏輯處理：判斷是否得分
        is_hit = logic.check_collision(wrist_pos)

        # C. 介面處理：把結果畫在畫面上
        # 我們把邏輯層的數據傳給 UI 層去畫
        ui.draw_game_elements(
            processed_image, 
            logic.target_pos, 
            logic.target_radius, 
            logic.score, 
            is_hit
        )

        # D. 顯示最終畫面
        cv2.imshow('Rehab System Modular Demo', processed_image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()