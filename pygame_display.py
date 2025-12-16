"""
Pygame 顯示模組 - 替代 OpenCV 的 imshow
提供更高效的畫面顯示和按鍵處理
"""

import os
import pygame
import cv2
import numpy as np

# 設定視窗位置到螢幕左上角
os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'


class PygameDisplay:
    """Pygame 顯示器 - 高效能畫面顯示"""
    
    def __init__(self, width=1920, height=1080, title="Rehab System - Rhythm Game", fullscreen=False):
        pygame.init()
        
        self.width = width
        self.height = height
        
        if fullscreen:
            self.screen = pygame.display.set_mode(
                (width, height), 
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            )
        else:
            self.screen = pygame.display.set_mode(
                (width, height), 
                pygame.NOFRAME | pygame.HWSURFACE | pygame.DOUBLEBUF
            )
        
        pygame.display.set_caption(title)
        self.should_quit = False
    
    def show(self, frame):
        """顯示 OpenCV 格式的畫面 (BGR)"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        surface = pygame.image.frombuffer(
            rgb_frame.tobytes(), 
            (rgb_frame.shape[1], rgb_frame.shape[0]),
            'RGB'
        )
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()
    
    def process_events(self):
        """處理 Pygame 事件，回傳是否應該關閉"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.should_quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    self.should_quit = True
        return self.should_quit
    
    def close(self):
        """關閉顯示器"""
        pygame.quit()

