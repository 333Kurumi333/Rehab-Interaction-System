import cv2
import random
import time
import os
import threading
from camera_sensor import PoseDetector
from new_game_logic import GameEngine
from ui_renderer import GameUI
from music_controller import MusicController

# === 1. Webcam 多執行緒 ===
class WebcamStream:
    def __init__(self, src=0, width=1920, height=1080):
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped: return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

# === 2. 背景影片多執行緒 ===
class VideoPlayerThread:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0 or self.fps > 120: self.fps = 30
        self.frame_duration = 1.0 / self.fps
        
        self.grabbed, self.frame = self.cap.read()
        self.stopped = False
        self.frame_available = True
        if not self.grabbed:
            print(f"無法讀取背景影片: {video_path}")
            self.frame_available = False

    def start(self):
        if self.frame_available:
            threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            start_time = time.time()
            grabbed, frame = self.cap.read()
            if not grabbed:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            self.grabbed, self.frame = grabbed, frame
            elapsed = time.time() - start_time
            wait_time = self.frame_duration - elapsed
            if wait_time > 0:
                time.sleep(wait_time)

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()

def is_hand_in_box(hand_pos, box_rect):
    if hand_pos is None: return False
    x, y = hand_pos
    x1, y1, x2, y2 = box_rect
    return x1 <= x <= x2 and y1 <= y <= y2

def main():
    SONG_LIST = [
        { "name": "Haruhikage", "filename": "Haruhikage_CRYCHIC.wav", "bpm": 97, "note_speed": 7, "folder": "music" },
        { "name": "Zankoku na Tenshi no Te-ze", "filename": "Zankoku na Tenshi no Te-ze.wav", "bpm": 128, "note_speed": 7, "folder": "music" }
    ]

    sensor = PoseDetector()
    FULL_WIDTH, FULL_HEIGHT = 1920, 1080
    ui = GameUI(width=FULL_WIDTH, height=FULL_HEIGHT)
    
    window_name = 'Rehab System - Rhythm Game'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    cap = WebcamStream(src=0, width=FULL_WIDTH, height=FULL_HEIGHT).start()
    time.sleep(1.0)
    
    is_running = True
    bg_video_thread = None
    
    # [新增] 初始化變數
    fps = 0
    prev_time = time.time()

    while is_running:
        # ==========================================
        # Phase 1: Menu (選單)
        # ==========================================
        if bg_video_thread:
            bg_video_thread.stop()
            bg_video_thread = None
            ui.background_video = None 

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

            processed_image, left_hand_pos, right_hand_pos = sensor.process_frame(frame)
            
            progress = 0.0
            if hover_index != -1:
                elapsed = time.time() - hover_start_time
                progress = min(elapsed / SELECTION_TIME, 1.0)
                if progress >= 1.0:
                    selected_song = SONG_LIST[hover_index]
                    menu_done = True 
            
            # [新增] 計算 FPS
            curr_time = time.time()
            if curr_time - prev_time > 0:
                fps = 1 / (curr_time - prev_time)
            else:
                fps = 0
            prev_time = curr_time

            # [修改] 傳入 fps
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
            
            if cv2.waitKey(1) & 0xFF == ord('q'): is_running = False
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1: is_running = False
        
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
        prev_time = time.time()
        
        while not game_done and is_running:
            ret, frame = cap.read()
            if not ret or frame is None: 
                time.sleep(0.001)
                continue
            
            processed_image, left_hand_pos, right_hand_pos = sensor.process_frame(frame)
            
            if bg_video_thread:
                bg_frame = bg_video_thread.read()
                if bg_frame is not None:
                    if bg_frame.shape[:2] != (FULL_HEIGHT, FULL_WIDTH):
                        bg_frame = cv2.resize(bg_frame, (FULL_WIDTH, FULL_HEIGHT))
                    
                    fg = cv2.bitwise_and(processed_image, ui.mask)
                    bg = cv2.bitwise_and(bg_frame, ui.mask_inv)
                    processed_image = cv2.add(fg, bg)

            logic.update_game_state(left_hand_pos, music_controller=music)
            logic.update_game_state(right_hand_pos, music_controller=music)
            
            if (time.time() - game_start_time > 2.0) and (not music.is_music_playing()):
                game_done = True

            notes_data = logic.get_notes_for_drawing()
            arc_info = logic.get_arc_info()
            score = logic.get_score()
            accuracy = logic.get_accuracy()
            combo = logic.get_combo() 
            
            # [新增] 計算 FPS
            curr_time = time.time()
            if curr_time - prev_time > 0:
                fps = 1 / (curr_time - prev_time)
            else:
                fps = 0
            prev_time = curr_time
            
            ui.draw_game_elements(
                processed_image,
                arc_info,
                notes_data,
                score,
                accuracy,
                combo=combo,
                song_name=selected_song['name'], # 傳入歌名
                fps=fps # 傳入 FPS
            )
            
            cv2.imshow(window_name, processed_image)
            
            if cv2.waitKey(1) & 0xFF == ord('q'): is_running = False
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1: is_running = False
            
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
            
            processed_image, left_hand_pos, right_hand_pos = sensor.process_frame(frame)
            
            progress = 0.0
            if is_hovering_btn:
                elapsed = time.time() - hover_start_time
                progress = min(elapsed / SELECTION_TIME, 1.0)
                if progress >= 1.0: result_done = True 
            
            # [新增] 計算 FPS
            curr_time = time.time()
            if curr_time - prev_time > 0:
                fps = 1 / (curr_time - prev_time)
            else:
                fps = 0
            prev_time = curr_time

            # [修改] 傳入 fps
            btn_rect = ui.draw_result_panel(processed_image, final_stats, progress, fps)
            
            if is_hand_in_box(left_hand_pos, btn_rect) or is_hand_in_box(right_hand_pos, btn_rect):
                if not is_hovering_btn: is_hovering_btn = True; hover_start_time = time.time()
            else:
                is_hovering_btn = False; hover_start_time = 0
            
            cv2.imshow(window_name, processed_image)
            
            if cv2.waitKey(1) & 0xFF == ord('q'): is_running = False
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1: is_running = False
                
    cap.stop()
    if bg_video_thread: bg_video_thread.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()