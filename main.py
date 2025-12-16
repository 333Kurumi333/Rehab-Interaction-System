import cv2
import time
import os
from camera_sensor import PoseDetectorThread
from new_game_logic import GameEngine
from ui_renderer import GameUI
from music_controller import MusicController
from webcam_stream import WebcamStream
from video_player import VideoPlayerThread
from utils import FPSCounter, check_window_close, is_hand_in_box, StepProfiler


def main():
    SONG_LIST = [
        { "name": "Haruhikage", "filename": "Haruhikage.wav", "bpm": 97, "note_speed": 7, "folder": "music" },
        { "name": "Zankoku na Tenshi no Te-ze", "filename": "Zankoku na Tenshi no Te-ze.wav", "bpm": 128, "note_speed": 7, "folder": "music" }
    ]

    sensor = PoseDetectorThread().start()
    FULL_WIDTH, FULL_HEIGHT = 1920, 1080
    ui = GameUI(width=FULL_WIDTH, height=FULL_HEIGHT)
    
    window_name = 'Rehab System - Rhythm Game'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    cap = WebcamStream(src=0, width=FULL_WIDTH, height=FULL_HEIGHT).start()
    time.sleep(1.0)
    
    is_running = True
    bg_video_thread = None
    fps_counter = FPSCounter()

    while is_running:
        # ==========================================
        # Phase 1: Menu (選單)
        # ==========================================
        if bg_video_thread:
            bg_video_thread.stop()
            bg_video_thread = None 

        selected_song = None
        hover_index = -1
        hover_start_time = 0
        SELECTION_TIME = 3.0
        
        menu_done = False
        while not menu_done and is_running:
            ret, frame = cap.read()
            if not ret or frame is None: 
                time.sleep(0.01)
                continue

            sensor.submit_frame(frame)
            processed_image, left_hand_pos, right_hand_pos = sensor.get_result()
            
            # 首次啟動時可能還沒有結果
            if processed_image is None:
                continue
            
            progress = 0.0
            if hover_index != -1:
                elapsed = time.time() - hover_start_time
                progress = min(elapsed / SELECTION_TIME, 1.0)
                if progress >= 1.0:
                    selected_song = SONG_LIST[hover_index]
                    menu_done = True 
            
            fps = fps_counter.update()
            box_regions = ui.draw_menu(processed_image, SONG_LIST, hover_index, progress, fps)
            
            current_hover = -1
            for i, box in enumerate(box_regions):
                if is_hand_in_box(left_hand_pos, box) or is_hand_in_box(right_hand_pos, box):
                    current_hover = i
                    break
            if current_hover != -1:
                if current_hover != hover_index:
                    hover_index = current_hover
                    hover_start_time = time.time()
            else:
                hover_index = -1
                hover_start_time = 0
            
            cv2.imshow(window_name, processed_image)
            if check_window_close(window_name): is_running = False
        
        if not is_running: break

        # ==========================================
        # Phase 2: Game (遊戲)
        # ==========================================
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if selected_song['folder']:
            music_path = os.path.join(current_dir, selected_song['folder'], selected_song['filename'])
        else:
            music_path = os.path.join(current_dir, selected_song['filename'])
        
        filename_no_ext = os.path.splitext(selected_song['filename'])[0]
        video_filename = f"{filename_no_ext}.mp4"
        video_path = os.path.join(current_dir, "video", video_filename)
        
        if os.path.exists(video_path):
            print(f"啟動背景影片執行緒: {video_filename}")
            bg_video_thread = VideoPlayerThread(video_path).start()
        else:
            bg_video_thread = None
        
        beatmap_name = filename_no_ext + ".txt"
        bpm = selected_song['bpm']
        note_speed = selected_song['note_speed'] 
        
        logic = GameEngine(
            width=FULL_WIDTH,
            height=FULL_HEIGHT,
            arc_radius=int(FULL_WIDTH * 0.4),
            zone_count=8,
            note_speed=note_speed,
            notes_per_beat=1,
            beatmap_file=beatmap_name 
        )
        music = MusicController(bpm=bpm, music_file=music_path)
        music.start()
        game_done = False
        game_start_time = time.time()
        profiler = StepProfiler(enabled=True, print_interval=60)  # 每 60 幀輸出一次
        
        while not game_done and is_running:
            profiler.start("攝影機讀取")
            ret, frame = cap.read()
            profiler.end()
            
            if not ret or frame is None: 
                time.sleep(0.001)
                continue
            
            profiler.start("姿態偵測")
            sensor.submit_frame(frame)
            processed_image, left_hand_pos, right_hand_pos = sensor.get_result()
            profiler.end()
            
            if processed_image is None:
                continue
            
            profiler.start("影片合成")
            if bg_video_thread:
                bg_frame = bg_video_thread.read()
                if bg_frame is not None:
                    if bg_frame.shape[:2] != (FULL_HEIGHT, FULL_WIDTH):
                        bg_frame = cv2.resize(bg_frame, (FULL_WIDTH, FULL_HEIGHT))
                    
                    fg = cv2.bitwise_and(processed_image, ui.mask)
                    bg = cv2.bitwise_and(bg_frame, ui.mask_inv)
                    processed_image = cv2.add(fg, bg)
            profiler.end()

            profiler.start("遊戲邏輯")
            logic.update_game_state(left_hand_pos, music_controller=music)
            logic.update_game_state(right_hand_pos, music_controller=music)
            profiler.end()
            
            if (time.time() - game_start_time > 2.0) and (not music.is_music_playing()):
                game_done = True

            notes_data = logic.get_notes_for_drawing()
            arc_info = logic.get_arc_info()
            score = logic.get_score()
            accuracy = logic.get_accuracy()
            combo = logic.get_combo() 
            
            profiler.start("UI渲染")
            fps = fps_counter.update()
            ui.draw_game_elements(
                processed_image, arc_info, notes_data, score, accuracy,
                combo=combo, song_name=selected_song['name'], fps=fps
            )
            profiler.end()
            
            profiler.start("畫面顯示")
            cv2.imshow(window_name, processed_image)
            if check_window_close(window_name): is_running = False
            profiler.end()
            
            profiler.frame_done()
            
        music.stop()
        if bg_video_thread:
            bg_video_thread.stop()
            
        if not is_running: break

        # ==========================================
        # Phase 3: Result (結算)
        # ==========================================
        final_stats = { 'total': logic.total_notes, 'hit': logic.hit_notes, 'miss': logic.miss_notes, 'combo': logic.max_combo, 'score': logic.score }
        result_done = False
        hover_start_time = 0
        is_hovering_btn = False
        
        while not result_done and is_running:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            
            sensor.submit_frame(frame)
            processed_image, left_hand_pos, right_hand_pos = sensor.get_result()
            
            if processed_image is None:
                continue
            
            progress = 0.0
            if is_hovering_btn:
                elapsed = time.time() - hover_start_time
                progress = min(elapsed / SELECTION_TIME, 1.0)
                if progress >= 1.0: result_done = True 
            
            fps = fps_counter.update()
            btn_rect = ui.draw_result_panel(processed_image, final_stats, progress, fps)
            
            if is_hand_in_box(left_hand_pos, btn_rect) or is_hand_in_box(right_hand_pos, btn_rect):
                if not is_hovering_btn: is_hovering_btn = True; hover_start_time = time.time()
            else:
                is_hovering_btn = False; hover_start_time = 0
            
            cv2.imshow(window_name, processed_image)
            if check_window_close(window_name): is_running = False
                
    sensor.stop()
    cap.stop()
    if bg_video_thread: bg_video_thread.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()