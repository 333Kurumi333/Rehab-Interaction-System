import cv2

class GameUI:
    def __init__(self):
        # 定義顏色 (Blue, Green, Red)
        self.COLOR_NORMAL = (0, 0, 255)   # 紅色
        self.COLOR_HIT = (0, 255, 0)      # 綠色
        self.TEXT_COLOR = (255, 0, 0)     # 藍色

    def draw_game_elements(self, image, target_pos, target_radius, score, is_hit):
        """
        將遊戲元素畫在影像上
        """
        # 決定目標顏色
        color = self.COLOR_HIT if is_hit else self.COLOR_NORMAL
        
        # 1. 畫目標圓圈
        cv2.circle(image, target_pos, target_radius, color, 3)
        
        # 2. 如果碰到，顯示 "HIT!"
        if is_hit:
            cv2.circle(image, target_pos, target_radius, color, -1) # 填滿
            cv2.putText(image, "HIT!", (target_pos[0]-20, target_pos[1]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 3. 畫分數看板
        cv2.putText(image, f"Score: {score}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.TEXT_COLOR, 3)