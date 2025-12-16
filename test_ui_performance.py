"""
OpenCV UI vs Pygame UI 效能比較測試
"""

import cv2
import pygame
import numpy as np
import time


def test_opencv_ui(frames=200):
    """測試 OpenCV UI 繪製"""
    print("\n🔵 測試 OpenCV UI 繪製...")
    
    # 模擬遊戲畫面
    test_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    times = []
    for i in range(frames):
        frame = test_frame.copy()
        start = time.time()
        
        # 模擬 UI 繪製
        # 1. 面板背景
        cv2.rectangle(frame, (0, 0), (1920, 100), (20, 20, 20), -1)
        
        # 2. 進度條
        cv2.rectangle(frame, (20, 90), (1900, 100), (30, 30, 30), -1)
        cv2.rectangle(frame, (20, 90), (1000, 100), (0, 200, 255), -1)
        
        # 3. 文字
        cv2.putText(frame, "SCORE: 12345", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        cv2.putText(frame, "Haruhikage", (800, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        cv2.putText(frame, "85.5%", (1750, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        
        # 4. 弧線
        cv2.ellipse(frame, (960, 1080), (700, 700), 0, 180, 360, (255, 255, 255), 2)
        
        # 5. 音符 (模擬 10 顆)
        for j in range(10):
            x = 300 + j * 140
            y = 400 + (j % 3) * 100
            cv2.circle(frame, (x+3, y+3), 30, (0, 0, 0), -1)
            cv2.circle(frame, (x, y), 30, (0, 0, 200), -1)
            cv2.circle(frame, (x, y), 30, (255, 255, 255), 2)
        
        # 6. Combo
        cv2.putText(frame, "15 COMBO", (800, 500), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 3)
        
        # 7. FPS
        cv2.putText(frame, "FPS: 45", (20, 1060), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    print(f"   平均: {avg:.2f} ms")
    return avg


def test_pygame_ui(frames=200):
    """測試 Pygame UI 繪製"""
    print("\n🟢 測試 Pygame UI 繪製...")
    
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.HIDDEN)
    
    font_large = pygame.font.SysFont('Arial', 48, bold=True)
    font_medium = pygame.font.SysFont('Arial', 36, bold=True)
    font_small = pygame.font.SysFont('Arial', 24)
    
    times = []
    for i in range(frames):
        screen.fill((0, 0, 0))
        start = time.time()
        
        # 模擬 UI 繪製
        # 1. 面板背景
        pygame.draw.rect(screen, (20, 20, 20), pygame.Rect(0, 0, 1920, 100))
        
        # 2. 進度條
        pygame.draw.rect(screen, (30, 30, 30), pygame.Rect(20, 90, 1880, 10))
        pygame.draw.rect(screen, (255, 200, 0), pygame.Rect(20, 90, 980, 10))
        
        # 3. 文字
        text1 = font_large.render("SCORE: 12345", True, (255, 255, 255))
        screen.blit(text1, (20, 20))
        
        text2 = font_medium.render("Haruhikage", True, (255, 255, 255))
        screen.blit(text2, (800, 25))
        
        text3 = font_medium.render("85.5%", True, (0, 255, 0))
        screen.blit(text3, (1750, 25))
        
        # 4. 弧線
        rect = pygame.Rect(960-700, 1080-700, 1400, 1400)
        pygame.draw.arc(screen, (255, 255, 255), rect, 0, 3.14159, 2)
        
        # 5. 音符 (模擬 10 顆)
        for j in range(10):
            x = 300 + j * 140
            y = 400 + (j % 3) * 100
            pygame.draw.circle(screen, (0, 0, 0), (x+3, y+3), 30)
            pygame.draw.circle(screen, (200, 0, 0), (x, y), 30)
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 30, 2)
        
        # 6. Combo
        text4 = font_large.render("15 COMBO", True, (0, 255, 255))
        screen.blit(text4, (800, 450))
        
        # 7. FPS
        text5 = font_small.render("FPS: 45", True, (0, 255, 0))
        screen.blit(text5, (20, 1050))
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    pygame.quit()
    
    avg = sum(times) / len(times)
    print(f"   平均: {avg:.2f} ms")
    return avg


if __name__ == "__main__":
    print("="*50)
    print("🎮 OpenCV UI vs Pygame UI 效能測試")
    print("   測試幀數: 200")
    print("="*50)
    
    opencv_time = test_opencv_ui(200)
    pygame_time = test_pygame_ui(200)
    
    print("\n" + "="*50)
    print("📊 結果比較")
    print("="*50)
    print(f"OpenCV UI:  {opencv_time:.2f} ms/幀")
    print(f"Pygame UI:  {pygame_time:.2f} ms/幀")
    
    if pygame_time < opencv_time:
        improvement = ((opencv_time - pygame_time) / opencv_time) * 100
        print(f"   → Pygame 比 OpenCV 快 {improvement:.1f}%")
    else:
        slower = ((pygame_time - opencv_time) / opencv_time) * 100
        print(f"   → Pygame 比 OpenCV 慢 {slower:.1f}%")
    print("="*50)
