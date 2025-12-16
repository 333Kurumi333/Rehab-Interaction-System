"""
OpenCV vs Pygame 顯示效能比較測試
測試 1920x1080 畫面的顯示速度
"""

import cv2
import numpy as np
import time

def test_opencv(frames=100):
    """測試 OpenCV imshow + waitKey"""
    print("\n🔵 測試 OpenCV...")
    
    # 創建測試畫面
    test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    cv2.namedWindow('OpenCV Test', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('OpenCV Test', 1920, 1080)
    
    times = []
    for i in range(frames):
        start = time.time()
        cv2.imshow('OpenCV Test', test_frame)
        cv2.waitKey(1)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        # 更新畫面內容（模擬遊戲）
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    cv2.destroyAllWindows()
    
    avg = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    fps = 1000 / avg
    
    print(f"   平均: {avg:.2f} ms")
    print(f"   最大: {max_time:.2f} ms")
    print(f"   最小: {min_time:.2f} ms")
    print(f"   理論 FPS: {fps:.1f}")
    
    return avg


def test_pygame(frames=100):
    """測試 Pygame 顯示"""
    print("\n🟢 測試 Pygame...")
    
    try:
        import pygame
    except ImportError:
        print("   ❌ Pygame 未安裝，請執行: pip install pygame")
        return None
    
    pygame.init()
    screen = pygame.display.set_mode((1920, 1080))
    pygame.display.set_caption('Pygame Test')
    
    # 創建測試畫面
    test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    times = []
    for i in range(frames):
        # 處理事件（必須，否則視窗無回應）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
        
        start = time.time()
        
        # OpenCV BGR -> Pygame RGB
        rgb_frame = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
        # 需要轉置因為 Pygame 是 (width, height)，NumPy 是 (height, width)
        rgb_frame = np.transpose(rgb_frame, (1, 0, 2))
        
        # 創建 Pygame surface 並顯示
        surface = pygame.surfarray.make_surface(rgb_frame)
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        # 更新畫面內容（模擬遊戲）
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    pygame.quit()
    
    avg = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    fps = 1000 / avg
    
    print(f"   平均: {avg:.2f} ms")
    print(f"   最大: {max_time:.2f} ms")
    print(f"   最小: {min_time:.2f} ms")
    print(f"   理論 FPS: {fps:.1f}")
    
    return avg


def test_pygame_optimized(frames=100):
    """測試 Pygame（優化版）"""
    print("\n🟡 測試 Pygame（優化版）...")
    
    try:
        import pygame
    except ImportError:
        print("   ❌ Pygame 未安裝")
        return None
    
    pygame.init()
    # 使用硬體加速
    screen = pygame.display.set_mode((1920, 1080), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption('Pygame Optimized Test')
    
    # 創建測試畫面
    test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    times = []
    for i in range(frames):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
        
        start = time.time()
        
        # 直接用 blit 更新（不做轉換，測試純顯示速度）
        rgb_frame = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.transpose(rgb_frame, (1, 0, 2))
        
        pygame.surfarray.blit_array(screen, rgb_frame)
        pygame.display.flip()
        
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    pygame.quit()
    
    avg = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    fps = 1000 / avg
    
    print(f"   平均: {avg:.2f} ms")
    print(f"   最大: {max_time:.2f} ms")
    print(f"   最小: {min_time:.2f} ms")
    print(f"   理論 FPS: {fps:.1f}")
    
    return avg


if __name__ == "__main__":
    print("="*50)
    print("🎮 OpenCV vs Pygame 顯示效能測試")
    print("   解析度: 1920x1080")
    print("   測試幀數: 100")
    print("="*50)
    
    opencv_time = test_opencv(100)
    pygame_time = test_pygame(100)
    pygame_opt_time = test_pygame_optimized(100)
    
    print("\n" + "="*50)
    print("📊 結果比較")
    print("="*50)
    print(f"OpenCV:           {opencv_time:.2f} ms/幀")
    if pygame_time:
        print(f"Pygame:           {pygame_time:.2f} ms/幀")
        improvement = ((opencv_time - pygame_time) / opencv_time) * 100
        print(f"   → 比 OpenCV {'快' if improvement > 0 else '慢'} {abs(improvement):.1f}%")
    if pygame_opt_time:
        print(f"Pygame (優化版):  {pygame_opt_time:.2f} ms/幀")
        improvement = ((opencv_time - pygame_opt_time) / opencv_time) * 100
        print(f"   → 比 OpenCV {'快' if improvement > 0 else '慢'} {abs(improvement):.1f}%")
    print("="*50)
