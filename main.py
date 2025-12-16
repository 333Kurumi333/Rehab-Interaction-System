import cv2
import time
import os
from camera_sensor import PoseDetectorThread
from new_game_logic import GameEngine
from ui_renderer import GameUI
from music_controller import MusicController
from webcam_stream import WebcamStream
from video_player import VideoPlayerThread
from utils import FPSCounter, is_hand_in_box, StepProfiler
from pygame_display import PygameDisplay
from pygame_ui import PygameUI


def main():
    SONG_LIST = [
        { "name": "Haruhikage", "filename": "Haruhikage.wav", "bpm": 97, "note_speed": 7, "folder": "music" },
        { "name": "Zankoku na Tenshi no Te-ze", "filename": "Zankoku na Tenshi no Te-ze.wav", "bpm": 128, "note_speed": 7, "folder": "music" }
    ]

    sensor = PoseDetectorThread().start()
    FULL_WIDTH, FULL_HEIGHT = 1920, 1080
    ui = GameUI(width=FULL_WIDTH, height=FULL_HEIGHT)
    pygame_ui = PygameUI(width=FULL_WIDTH, height=FULL_HEIGHT)  # 新增 Pygame UI
    
    # 使用 Pygame 顯示器（替代 OpenCV imshow）
    display = PygameDisplay(FULL_WIDTH, FULL_HEIGHT, 'Rehab System - Rhythm Game')
    
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
            
            display.show(processed_image)
            if display.process_events(): is_running = False
        
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
        
        # 平行處理追蹤
        last_pose_id = -1
        pose_reuse_count = 0
        total_frames = 0
        
        # 時間驅動：計算 delta_time
        last_frame_time = time.time()
        
        while not game_done and is_running:
            # 計算這一幀經過的時間
            current_time = time.time()
            delta_time = current_time - last_frame_time
            last_frame_time = current_time
            
            profiler.start("攝影機讀取")
            ret, frame = cap.read()
            profiler.end()
            
            if not ret or frame is None: 
                time.sleep(0.001)
                continue
            
            profiler.start("姿態偵測")
            sensor.submit_frame(frame)
            processed_image, left_hand_pos, right_hand_pos, pose_id, pose_time = sensor.get_result_with_stats()
            profiler.end()
            
            # 追蹤重複使用
            if pose_id == last_pose_id:
                pose_reuse_count += 1
            last_pose_id = pose_id
            total_frames += 1
            
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
            # 時間驅動：傳入 delta_time
            logic.update_game_state(left_hand_pos, delta_time, music_controller=music)
            logic.update_game_state(right_hand_pos, delta_time, music_controller=music)
            profiler.end()
            
            if (time.time() - game_start_time > 2.0) and (not music.is_music_playing()):
                game_done = True

            notes_data = logic.get_notes_for_drawing()
            arc_info = logic.get_arc_info()
            score = logic.get_score()
            accuracy = logic.get_accuracy()
            combo = logic.get_combo() 
            
            # 計算時間進度（使用音樂播放位置）
            time_progress = music.get_progress()
            
            profiler.start("UI渲染")
            fps = fps_counter.update()
            profiler.end()
            
            profiler.start("畫面顯示")
            # 新流程：先 blit 基底畫面，再用 Pygame 繪製 UI
            display.blit_frame(processed_image)
            pygame_ui.draw_game_ui(
                display.get_screen(), arc_info, notes_data, score, accuracy,
                combo, selected_song['name'], fps, time_progress
            )
            display.flip()
            if display.process_events(): is_running = False
            profiler.end()
            
            # 每 60 幀輸出平行處理統計
            if profiler.frame_count == 0 and total_frames > 0:
                print("\n" + "="*50)
                print("🔄 平行處理統計")
                print("="*50)
                
                # 攝影機統計
                cam_stats = cap.get_stats()
                print(f"攝影機執行緒: 讀取 {cam_stats['read_count']} 幀, 平均 {cam_stats['avg_time_ms']:.1f} ms/幀")
                
                # 姿態偵測統計
                pose_stats = sensor.get_stats()
                print(f"姿態偵測執行緒: 處理 {pose_stats['process_count']} 幀, 平均 {pose_stats['avg_time_ms']:.1f} ms/幀")
                
                # 影片統計
                if bg_video_thread:
                    vid_stats = bg_video_thread.get_stats()
                    print(f"影片播放執行緒: 讀取 {vid_stats['read_count']} 幀, 平均 {vid_stats['avg_time_ms']:.1f} ms/幀")
                
                # 重複使用統計
                reuse_rate = (pose_reuse_count / total_frames * 100) if total_frames > 0 else 0
                print(f"\n姿態結果重複使用: {pose_reuse_count}/{total_frames} 次 ({reuse_rate:.1f}%)")
                print("="*50)
            
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
            
            display.show(processed_image)
            if display.process_events(): is_running = False
                
    sensor.stop()
    cap.stop()
    if bg_video_thread: bg_video_thread.stop()
    display.close()

if __name__ == "__main__":
    main()