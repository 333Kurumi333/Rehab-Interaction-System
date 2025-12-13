import cv2
import random
import time
# 匯入另外四個檔案的 Class
from camera_sensor import PoseDetector
from new_game_logic import GameEngine
from ui_renderer import GameUI
from music_controller import MusicController

def main():
    # 選擇關卡
    print("=" * 50)
    print("歡迎來到復健互動遊戲！")
    print("=" * 50)
    print("請選擇關卡：")
    print("1. 第一關 - 基礎模式")
    print("   - BPM: 100 (慢)")
    print("   - 每次 1 個物件")
    print("   - 只有紅色物件")
    print()
    print("2. 第二關 - 進階模式")
    print("   - BPM: 110 (稍快)")
    print("   - 每次 2 個物件（不重疊）")
    print("   - 紅色：正常擊中 (+1分) 80%")
    print("   - 藍色：炸彈，不能碰 (-2分) 15%")
    print("   - 金色：加分物件 (+2分) 5%")
    print("=" * 50)

    while True:
        level_input = input("請輸入關卡編號 (1 或 2): ").strip()
        if level_input in ['1', '2']:
            level = int(level_input)
            break
        print("請輸入 1 或 2")

    # 根據關卡設定參數
    if level == 1:
        bpm = 60  # 降低節奏 (120 -> 100)
        notes_per_beat = 1
        note_speed = 7  # 稍微降速 (8 -> 7)
    else:  # level == 2
        bpm = 80  # 大幅降低節奏 (140 -> 110)
        notes_per_beat = 1  # 固定每次 1 個物件
        note_speed = 8  # 降低速度 (9 -> 8)

    print(f"\n開始第 {level} 關！")
    print("按 'q' 可以退出遊戲")
    print()

    # 1. 啟動各個模組
    sensor = PoseDetector()  # 視覺模組

    # 設定視窗名稱 (要跟後面 imshow 的名稱一模一樣)
    window_name = 'Rehab System - Rhythm Game'
    
    # 告訴 OpenCV：這個視窗是可以自由縮放的 (WINDOW_NORMAL)
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # 直接設定視窗一開始就全螢幕
    #cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # 開啟攝影機以取得解析度
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)


    time.sleep(1) 
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 10000)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 10000)
    
    # 讀取實際設定結果
    real_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"已設定攝影機解析度: {real_width}x{real_height} (低延遲模式)")
    ret, frame = cap.read()
    retry_count = 0
    while not ret and retry_count < 5:
        print(f"嘗試讀取攝影機... ({retry_count + 1}/5)")
        time.sleep(0.5)
        ret, frame = cap.read()
        retry_count += 1

    if not ret:
        print("無法開啟攝影機")
        print("請檢查：")
        print("1. 是否有其他程式正在使用攝影機")
        print("2. 系統設定 > 隱私權與安全性 > 相機 中是否允許 Python/終端機存取")
        cap.release()
        return

    # 取得攝影機解析度
    height, width = frame.shape[:2]

    # 初始化遊戲邏輯（需要畫面尺寸）
    logic = GameEngine(
        width=width,
        height=height,
        arc_radius=int(width * 0.4),
        zone_count=8,
        note_speed=note_speed,
        level=level,
        notes_per_beat=notes_per_beat
    )
    ui = GameUI()  # 介面模組

    # 初始化音樂控制器
    music = MusicController(
        bpm=bpm,
        music_file="sunds@1208.mp3"  # 背景音樂
    )
    music.start()

    print(f"音樂節奏: {bpm} BPM | 每拍物件數: {notes_per_beat}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # A. 視覺處理：取得影像與雙手手掌座標
        processed_image, left_hand_pos, right_hand_pos = sensor.process_frame(frame)

        # B. 邏輯處理：更新遊戲狀態（物件生成、移動、碰撞判定）
        # 傳入雙手座標和音樂控制器，遊戲邏輯會檢查兩隻手並跟隨節奏
        logic.update_game_state(left_hand_pos, music_controller=music)
        logic.update_game_state(right_hand_pos, music_controller=music)

        # C. 介面處理：把結果畫在畫面上
        # 取得遊戲資料
        notes_data = logic.get_notes_for_drawing()
        arc_info = logic.get_arc_info()
        score = logic.get_score()
        accuracy = logic.get_accuracy()

        combo = logic.get_combo() 

        # 繪製遊戲元素
        ui.draw_game_elements(
            processed_image,
            arc_info,
            notes_data,
            score,
            accuracy,
            level,
            combo=combo  # combo
        )


        # 繪製遊戲元素
        ui.draw_game_elements(
            processed_image,
            arc_info,
            notes_data,
            score,
            accuracy,
            level
        )

        # D. 顯示最終畫面
        cv2.imshow('Rehab System - Rhythm Game', processed_image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

        # 檢查視窗是否在剛才的 waitKey 過程中被 "X" 關閉了
        # 這行必須放在 waitKey 之後
        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            print("視窗已關閉")
            break

    cap.release()
    cv2.destroyAllWindows()
    music.stop()  # 停止音樂

if __name__ == "__main__":
    main()