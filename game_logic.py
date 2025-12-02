import math

class GameEngine:
    def __init__(self):
        # 遊戲初始設定
        self.target_pos = (150, 150) # 目標位置
        self.target_radius = 50      # 目標大小
        self.score = 0               # 分數
        self.is_hit = False          # 狀態：是否正在接觸中

    def check_collision(self, hand_pos):
        """
        判斷手是否碰到目標
        回傳: True (碰到), False (沒碰到)
        """
        if hand_pos is None:
            self.is_hit = False
            return False

        # 計算距離公式 (毕氏定理)
        distance = math.sqrt(
            (hand_pos[0] - self.target_pos[0])**2 + 
            (hand_pos[1] - self.target_pos[1])**2
        )

        if distance < self.target_radius:
            if not self.is_hit: # 避免持續接觸時一直加分
                self.score += 1
                self.is_hit = True
            return True
        else:
            self.is_hit = False
            return False