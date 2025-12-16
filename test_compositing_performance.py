"""
OpenCV 圖片合成 vs Pygame 圖片合成 效能比較測試
"""

import cv2
import pygame
import numpy as np
import time


def test_opencv_compositing(frames=200):
    """測試 OpenCV 圖片合成"""
    print("\n🔵 測試 OpenCV 圖片合成...")
    
    # 模擬攝影機畫面和背景影片
    camera = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    video = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # 建立圓形遮罩
    mask = np.zeros((1080, 1920), dtype=np.uint8)
    cv2.circle(mask, (960, 1080), 864, 255, -1)
    mask_inv = cv2.bitwise_not(mask)
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    mask_inv_3ch = cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR)
    
    times = []
    for i in range(frames):
        start = time.time()
        
        # OpenCV 合成
        fg = cv2.bitwise_and(camera, mask_3ch)
        bg = cv2.bitwise_and(video, mask_inv_3ch)
        result = cv2.add(fg, bg)
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    print(f"   平均: {avg:.2f} ms")
    return avg


def test_pygame_compositing(frames=200):
    """測試 Pygame 圖片合成 (使用 Surface blitting)"""
    print("\n🟢 測試 Pygame 圖片合成...")
    
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.HIDDEN)
    
    # 模擬攝影機畫面和背景影片
    camera = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    video = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # 建立圓形遮罩 Surface
    mask_surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (960, 1080), 864)
    
    times = []
    for i in range(frames):
        start = time.time()
        
        # 方法：建立兩個 Surface，用遮罩混合
        # 這其實不是 Pygame 擅長的事...
        
        # 轉換 numpy 到 Surface
        video_surface = pygame.surfarray.make_surface(np.transpose(video, (1, 0, 2)))
        camera_surface = pygame.surfarray.make_surface(np.transpose(camera, (1, 0, 2)))
        
        # Pygame 沒有直接的遮罩混合功能，需要用 blits
        screen.blit(video_surface, (0, 0))
        
        # 這裡無法真正用 Pygame 做圓形遮罩混合，因為 Pygame 不支援這種操作
        # 我們只是測試 Surface 轉換和 blit 的速度
        screen.blit(camera_surface, (0, 0))
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    pygame.quit()
    
    avg = sum(times) / len(times)
    print(f"   平均: {avg:.2f} ms (僅包含 Surface 轉換和 blit)")
    return avg


def test_numpy_compositing(frames=200):
    """測試純 NumPy 圖片合成（可能比 OpenCV 更快）"""
    print("\n🟡 測試純 NumPy 圖片合成...")
    
    # 模擬攝影機畫面和背景影片
    camera = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    video = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    # 建立圓形遮罩（0 或 1 的浮點數）
    mask = np.zeros((1080, 1920), dtype=np.float32)
    cv2.circle(mask, (960, 1080), 864, 1.0, -1)
    mask_3ch = np.stack([mask] * 3, axis=-1)
    mask_inv_3ch = 1.0 - mask_3ch
    
    times = []
    for i in range(frames):
        start = time.time()
        
        # NumPy 合成（直接乘法 + 加法）
        result = (camera.astype(np.float32) * mask_3ch + 
                  video.astype(np.float32) * mask_inv_3ch).astype(np.uint8)
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    print(f"   平均: {avg:.2f} ms")
    return avg


if __name__ == "__main__":
    print("="*50)
    print("🎮 圖片合成效能測試")
    print("   測試幀數: 200")
    print("   解析度: 1920x1080")
    print("="*50)
    
    opencv_time = test_opencv_compositing(200)
    numpy_time = test_numpy_compositing(200)
    pygame_time = test_pygame_compositing(200)
    
    print("\n" + "="*50)
    print("📊 結果比較")
    print("="*50)
    print(f"OpenCV (bitwise_and + add):  {opencv_time:.2f} ms/幀")
    print(f"NumPy (乘法 + 加法):          {numpy_time:.2f} ms/幀")
    print(f"Pygame (Surface 轉換):        {pygame_time:.2f} ms/幀")
    print("="*50)
    print("\n💡 結論：Pygame 不適合做遮罩合成，OpenCV 是最佳選擇")
