import pygame
import time

class MusicController:
    """
    音樂控制器：處理背景音樂播放和節奏同步
    """

    def __init__(self, bpm=120, music_file=None):
        """
        初始化音樂控制器

        參數:
        bpm: 每分鐘節拍數 (Beats Per Minute)，預設 120
        music_file: 音樂檔案路徑 (mp3/wav)，可選
        """
        pygame.mixer.init()

        self.bpm = bpm
        self.beat_interval = 60.0 / bpm  # 每個節拍的時間間隔（秒）
        self.music_file = music_file

        # 節奏追蹤
        self.start_time = None
        self.is_playing = False
        self.current_beat = 0

        # 如果有音樂檔案，載入它
        if music_file:
            try:
                pygame.mixer.music.load(music_file)
                print(f"音樂載入成功: {music_file}")
            except Exception as e:
                print(f"音樂載入失敗: {e}")
                self.music_file = None

    def start(self):
        """開始播放音樂和節奏計時"""
        self.start_time = time.time()
        self.is_playing = True
        self.current_beat = 0

        # 如果有音樂檔案，播放它（循環播放）
        if self.music_file:
            try:
                pygame.mixer.music.play(-1)  # -1 表示循環播放
                print("音樂開始播放")
            except Exception as e:
                print(f"音樂播放失敗: {e}")

    def stop(self):
        """停止音樂"""
        self.is_playing = False
        if self.music_file:
            pygame.mixer.music.stop()

    def should_spawn_note(self):
        """
        判斷現在是否應該生成物件（根據節拍）

        回傳: True 如果現在是節拍點，False 否則
        """
        if not self.is_playing or self.start_time is None:
            return False

        # 計算經過的時間
        elapsed_time = time.time() - self.start_time

        # 計算現在應該在第幾拍
        expected_beat = int(elapsed_time / self.beat_interval)

        # 如果節拍數增加了，代表到了新的節拍點
        if expected_beat > self.current_beat:
            self.current_beat = expected_beat
            return True

        return False

    def get_current_beat(self):
        """取得目前的節拍數"""
        return self.current_beat

    def set_bpm(self, bpm):
        """設定新的 BPM"""
        self.bpm = bpm
        self.beat_interval = 60.0 / bpm
