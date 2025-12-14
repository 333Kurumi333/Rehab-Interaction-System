import pygame
import time

class MusicController:
    def __init__(self, bpm=120, music_file=None):
        pygame.mixer.init()

        self.bpm = bpm
        self.beat_interval = 60.0 / bpm
        self.music_file = music_file
        self.start_time = None
        self.is_playing = False
        self.current_beat = 0

        if music_file:
            try:
                pygame.mixer.music.load(music_file)
                print(f"音樂載入成功: {music_file}")
            except Exception as e:
                print(f"音樂載入失敗: {e}")
                self.music_file = None

    def start(self):
        """開始播放音樂"""
        self.start_time = time.time()
        self.is_playing = True
        self.current_beat = 0

        if self.music_file:
            try:
                # === 修改重點：改成只播放 1 次 (loop=0)，不是 -1 (無限循環) ===
                pygame.mixer.music.play(0)
                print("音樂開始播放")
            except Exception as e:
                print(f"音樂播放失敗: {e}")

    def stop(self):
        self.is_playing = False
        if self.music_file:
            pygame.mixer.music.stop()

    def should_spawn_note(self):
        if not self.is_playing or self.start_time is None:
            return False
        elapsed_time = time.time() - self.start_time
        expected_beat = int(elapsed_time / self.beat_interval)
        if expected_beat > self.current_beat:
            self.current_beat = expected_beat
            return True
        return False

    def get_current_beat_float(self):
        if not self.is_playing or self.start_time is None:
            return 0.0
        elapsed_time = time.time() - self.start_time
        return elapsed_time / self.beat_interval

    # === 新增功能：檢查音樂是否還在播放 ===
    def is_music_playing(self):
        """
        回傳 True 代表音樂還在播
        回傳 False 代表音樂播完了 (或根本沒播)
        """
        if not self.music_file: 
            return False
        
        # get_busy() 回傳 True 代表正在混音(播放中)
        return pygame.mixer.music.get_busy()