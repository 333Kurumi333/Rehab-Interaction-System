import cv2
import time


class FPSCounter:
    """FPS 計算器"""
    
    def __init__(self):
        self.prev_time = time.time()
        self.fps = 0
    
    def update(self):
        curr = time.time()
        self.fps = 1 / (curr - self.prev_time) if curr > self.prev_time else 0
        self.prev_time = curr
        return self.fps


def check_window_close(window_name):
    """檢查視窗是否應關閉"""
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return True
    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
        return True
    return False


def is_hand_in_box(hand_pos, box_rect):
    """檢查手部位置是否在矩形區域內"""
    if hand_pos is None:
        return False
    x, y = hand_pos
    x1, y1, x2, y2 = box_rect
    return x1 <= x <= x2 and y1 <= y <= y2


class StepProfiler:
    """步驟計時器 - 用於分析各步驟耗時找出 bottleneck"""
    
    def __init__(self, enabled=True, print_interval=60):
        self.enabled = enabled
        self.print_interval = print_interval  # 每幾幀輸出一次
        self.frame_count = 0
        self.step_times = {}
        self.step_start = None
        self.current_step = None
    
    def start(self, step_name):
        """開始計時某個步驟"""
        if not self.enabled:
            return
        self.current_step = step_name
        self.step_start = time.time()
    
    def end(self):
        """結束當前步驟計時"""
        if not self.enabled or self.step_start is None:
            return
        elapsed = (time.time() - self.step_start) * 1000  # 轉成毫秒
        if self.current_step not in self.step_times:
            self.step_times[self.current_step] = []
        self.step_times[self.current_step].append(elapsed)
        self.step_start = None
    
    def frame_done(self):
        """一幀結束，檢查是否需要輸出報告"""
        if not self.enabled:
            return
        self.frame_count += 1
        if self.frame_count >= self.print_interval:
            self.print_report()
            self.reset()
    
    def print_report(self):
        """輸出耗時報告"""
        print("\n" + "="*50)
        print(f"⏱️  步驟耗時分析 (過去 {self.frame_count} 幀平均值)")
        print("="*50)
        total = 0
        for step, times in self.step_times.items():
            avg = sum(times) / len(times)
            total += avg
            bar = "█" * int(avg / 2)  # 視覺化長條
            print(f"{step:20s}: {avg:6.2f} ms {bar}")
        print("-"*50)
        print(f"{'總計':20s}: {total:6.2f} ms (≈ {1000/total:.1f} FPS)")
        print("="*50 + "\n")
    
    def reset(self):
        """重置計數"""
        self.frame_count = 0
        self.step_times = {}

