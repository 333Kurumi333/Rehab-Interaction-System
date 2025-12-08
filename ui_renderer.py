import cv2
import math

class GameUI:
    def __init__(self):
        # 定義顏色 (BGR 格式)
        self.COLOR_ARC = (200, 200, 200)      # 灰色 - 半圓軌道
        self.COLOR_ZONE_LINE = (150, 150, 150)  # 淺灰色 - 區域分隔線
        self.COLOR_NOTE_ACTIVE = (0, 0, 255)  # 紅色 - 活動中的物件
        self.COLOR_NOTE_HIT = (0, 255, 0)     # 綠色 - 打中的物件
        self.COLOR_NOTE_MISS = (128, 128, 128) # 深灰色 - 錯過的物件
        self.TEXT_COLOR = (255, 255, 255)     # 白色 - 文字

    def draw_game_elements(self, image, arc_info, notes_data, score):
        """
        將新遊戲的元素畫在影像上

        參數:
        image: 要繪製的影像
        arc_info: 半圓資訊 (包含中心點、半徑、區域數量等)
        notes_data: 所有物件的繪圖資訊列表
        score: 目前分數
        """
        # 1. 繪製半圓軌道
        self._draw_arc(image, arc_info)

        # 2. 繪製區域分隔線
        self._draw_zone_lines(image, arc_info)

        # 3. 繪製所有物件 (notes)
        self._draw_notes(image, notes_data)

        # 4. 繪製分數看板
        self._draw_score(image, score)

    def _draw_arc(self, image, arc_info):
        """繪製半圓軌道"""
        center = arc_info['center']
        radius = arc_info['radius']

        # 畫半圓 (從 0 度到 180 度)
        # OpenCV 的 ellipse 角度是順時針，0度在右邊
        cv2.ellipse(
            image,
            center,
            (radius, radius),
            0,              # 旋轉角度
            180,            # 起始角度 (從左邊開始)
            360,            # 結束角度 (到右邊結束)
            self.COLOR_ARC,
            5               # 線條粗細（加粗讓軌道更明顯）
        )

    def _draw_zone_lines(self, image, arc_info):
        """繪製區域分隔線"""
        center = arc_info['center']
        radius = arc_info['radius']
        zone_count = arc_info['zone_count']
        zone_angle_width = arc_info['zone_angle_width']

        for i in range(1, zone_count):
            # 計算分隔線的角度
            angle = 180 - (i * zone_angle_width)
            rad_angle = math.radians(angle)

            # 計算分隔線的端點
            end_x = int(center[0] + radius * math.cos(rad_angle))
            end_y = int(center[1] - radius * math.sin(rad_angle))

            # 畫線
            cv2.line(image, center, (end_x, end_y), self.COLOR_ZONE_LINE, 1)

    def _draw_notes(self, image, notes_data):
        """繪製所有物件"""
        for note in notes_data:
            pos = note['pos']
            radius = note['radius']
            status = note['status']

            # 根據狀態選擇顏色
            if status == 'hit':
                color = self.COLOR_NOTE_HIT
            elif status == 'miss':
                color = self.COLOR_NOTE_MISS
            else:
                color = self.COLOR_NOTE_ACTIVE

            # 繪製物件（實心圓）
            cv2.circle(image, pos, radius, color, -1)

            # 如果打中了，額外顯示 "HIT!" 文字
            if status == 'hit':
                cv2.putText(
                    image,
                    "HIT!",
                    (pos[0] - 30, pos[1] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    self.COLOR_NOTE_HIT,
                    2
                )

    def _draw_score(self, image, score):
        """繪製分數看板"""
        cv2.putText(
            image,
            f"Score: {score}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            self.TEXT_COLOR,
            3
        )