"""
Pygame UI 渲染器 - 測試用 Pygame 繪製 UI 是否比 OpenCV 更快
"""

import pygame
import math


class PygameUI:
    """使用 Pygame 繪製 UI 元素"""
    
    def __init__(self, width=1920, height=1080):
        self.width = width
        self.height = height
        
        # 初始化字體
        pygame.font.init()
        self.font_large = pygame.font.SysFont('Arial', 48, bold=True)
        self.font_medium = pygame.font.SysFont('Arial', 36, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 24)
        
        # 顏色定義 (RGB for Pygame)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_GREEN = (0, 255, 0)
        self.COLOR_RED = (255, 0, 0)
        self.COLOR_YELLOW = (255, 255, 0)
        self.COLOR_CYAN = (0, 255, 255)
        self.COLOR_ORANGE = (255, 200, 0)
    
    def draw_game_ui(self, screen, arc_info, notes_data, score, accuracy, combo, song_name, fps, time_progress):
        """在 Pygame screen 上繪製遊戲 UI"""
        # 繪製頂部面板
        self._draw_dashboard(screen, score, accuracy, song_name, time_progress)
        
        # 繪製遊戲弧線
        self._draw_arc(screen, arc_info)
        
        # 繪製音符
        self._draw_notes(screen, notes_data)
        
        # 繪製連擊
        if combo > 1:
            self._draw_combo(screen, combo)
        
        # 繪製 FPS
        self._draw_fps(screen, fps)
    
    def _draw_dashboard(self, screen, score, accuracy, song_name, time_progress):
        """繪製頂部儀表板"""
        w, h = self.width, 100
        
        # 背景面板
        panel_rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(screen, (20, 20, 20), panel_rect)
        
        # 時間進度條
        bar_bg = pygame.Rect(20, h - 10, w - 40, 10)
        pygame.draw.rect(screen, (30, 30, 30), bar_bg)
        
        bar_width = int((w - 40) * min(time_progress, 1.0))
        if bar_width > 0:
            bar_fg = pygame.Rect(20, h - 10, bar_width, 10)
            pygame.draw.rect(screen, self.COLOR_ORANGE, bar_fg)
        
        # Score
        score_text = self.font_large.render(f"SCORE: {score}", True, self.COLOR_WHITE)
        screen.blit(score_text, (20, 20))
        
        # 歌名
        if song_name:
            song_text = self.font_medium.render(song_name, True, self.COLOR_WHITE)
            song_x = (w - song_text.get_width()) // 2
            screen.blit(song_text, (song_x, 25))
        
        # 命中率
        if accuracy is not None:
            acc_color = self.COLOR_GREEN if accuracy > 80 else self.COLOR_RED
            acc_text = self.font_medium.render(f"{accuracy:.1f}%", True, acc_color)
            screen.blit(acc_text, (w - acc_text.get_width() - 30, 25))
    
    def _draw_arc(self, screen, arc_info):
        """繪製遊戲弧線"""
        center = arc_info['center']
        radius = arc_info['radius']
        zone_count = arc_info['zone_count']
        zone_angle_width = arc_info['zone_angle_width']
        
        # 繪製主弧線
        rect = pygame.Rect(
            center[0] - radius, 
            center[1] - radius, 
            radius * 2, 
            radius * 2
        )
        pygame.draw.arc(screen, self.COLOR_WHITE, rect, 0, math.pi, 2)
        
        # 繪製區域分隔線
        for i in range(1, zone_count):
            angle = math.radians(180 - (i * zone_angle_width))
            inner_r, outer_r = radius - 100, radius + 100
            start = (int(center[0] + inner_r * math.cos(angle)), 
                     int(center[1] - inner_r * math.sin(angle)))
            end = (int(center[0] + outer_r * math.cos(angle)), 
                   int(center[1] - outer_r * math.sin(angle)))
            pygame.draw.line(screen, (100, 100, 100), start, end, 2)
    
    def _draw_notes(self, screen, notes_data):
        """繪製音符"""
        for note in notes_data:
            pos = note['pos']
            radius = int(note['radius'])
            status = note['status']
            note_type = note.get('type', 'normal')
            
            # 選擇顏色
            if status == 'hit':
                color = self.COLOR_GREEN
            elif status == 'miss':
                color = self.COLOR_RED
            elif note_type == 'bonus':
                color = self.COLOR_YELLOW
            else:
                color = (200, 50, 50)  # 紅色
            
            # 繪製陰影
            pygame.draw.circle(screen, self.COLOR_BLACK, (pos[0]+3, pos[1]+3), radius)
            # 繪製主體
            pygame.draw.circle(screen, color, pos, radius)
            # 繪製邊框
            pygame.draw.circle(screen, self.COLOR_WHITE, pos, radius, 2)
    
    def _draw_combo(self, screen, combo):
        """繪製連擊數"""
        combo_text = self.font_large.render(f"{combo} COMBO", True, self.COLOR_CYAN)
        x = (self.width - combo_text.get_width()) // 2
        y = self.height // 2 - 100
        screen.blit(combo_text, (x, y))
    
    def _draw_fps(self, screen, fps):
        """繪製 FPS"""
        fps_text = self.font_small.render(f"FPS: {int(fps)}", True, self.COLOR_GREEN)
        screen.blit(fps_text, (20, self.height - 30))
