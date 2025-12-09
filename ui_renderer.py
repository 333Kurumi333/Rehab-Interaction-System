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
        self.COLOR_NOTE_BOMB = (255, 100, 0)  # 藍色 - 炸彈物件
        self.COLOR_NOTE_BONUS = (0, 215, 255) # 金色 - 加分物件 (BGR: 金黃色)
        self.COLOR_NOTE_BOMB_HIT = (100, 100, 100) # 深灰 - 碰到炸彈
        self.TEXT_COLOR = (255, 255, 255)     # 白色 - 文字

    def draw_game_elements(self, image, arc_info, notes_data, score, accuracy=None, level=1):
        """
        將新遊戲的元素畫在影像上

        參數:
        image: 要繪製的影像
        arc_info: 半圓資訊 (包含中心點、半徑、區域數量等)
        notes_data: 所有物件的繪圖資訊列表
        score: 目前分數
        accuracy: 準確率（百分比）
        level: 目前關卡
        """
        # 1. 繪製半圓軌道
        self._draw_arc(image, arc_info)

        # 2. 繪製區域分隔線
        self._draw_zone_lines(image, arc_info)

        # 3. 繪製所有物件 (notes)
        self._draw_notes(image, notes_data)

        # 4. 繪製分數看板和關卡
        self._draw_score(image, score, level)

        # 5. 繪製準確率（右上角）
        if accuracy is not None:
            self._draw_accuracy(image, accuracy)

        # 6. 如果是第二關，顯示物件說明
        if level >= 2:
            self._draw_legend(image)

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
            note_type = note.get('type', 'normal')

            # 根據狀態和類型選擇顏色
            if status == 'hit':
                color = self.COLOR_NOTE_HIT
            elif status == 'bomb_hit':
                color = self.COLOR_NOTE_BOMB_HIT
            elif status == 'miss':
                color = self.COLOR_NOTE_MISS
            elif note_type == 'bomb':
                color = self.COLOR_NOTE_BOMB
            elif note_type == 'bonus':
                color = self.COLOR_NOTE_BONUS
            else:
                color = self.COLOR_NOTE_ACTIVE

            # 繪製物件（實心圓）
            cv2.circle(image, pos, radius, color, -1)

            # 根據狀態顯示文字提示
            if status == 'hit':
                if note_type == 'bonus':
                    cv2.putText(
                        image,
                        "+2!",
                        (pos[0] - 20, pos[1] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        self.COLOR_NOTE_BONUS,
                        2
                    )
                else:
                    cv2.putText(
                        image,
                        "HIT!",
                        (pos[0] - 30, pos[1] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        self.COLOR_NOTE_HIT,
                        2
                    )
            elif status == 'bomb_hit':
                cv2.putText(
                    image,
                    "-2!",
                    (pos[0] - 20, pos[1] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),  # 紅色警告
                    2
                )

    def _draw_score(self, image, score, level=1):
        """繪製分數看板和關卡"""
        # 顯示關卡
        cv2.putText(
            image,
            f"Level {level}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (100, 200, 255),  # 橘色
            3
        )
        # 顯示分數
        cv2.putText(
            image,
            f"Score: {score}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            self.TEXT_COLOR,
            3
        )

    def _draw_accuracy(self, image, accuracy):
        """繪製準確率（右上角）"""
        height, width = image.shape[:2]
        text = f"Accuracy: {accuracy:.1f}%"

        # 計算文字大小以便右對齊
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.5
        thickness = 3
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

        # 右上角位置（留一些邊距）
        x = width - text_size[0] - 20
        y = 50

        cv2.putText(
            image,
            text,
            (x, y),
            font,
            font_scale,
            self.TEXT_COLOR,
            thickness
        )

    def _draw_legend(self, image):
        """繪製物件說明（第二關）"""
        height, width = image.shape[:2]

        # 說明框的位置（左下角）
        start_x = 20
        start_y = height - 150
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        line_height = 35

        # 繪製半透明背景（可選）
        # overlay = image.copy()
        # cv2.rectangle(overlay, (start_x - 10, start_y - 10), (start_x + 300, start_y + 120), (0, 0, 0), -1)
        # cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)

        # 紅色物件說明
        cv2.circle(image, (start_x + 15, start_y + 10), 12, self.COLOR_NOTE_ACTIVE, -1)
        cv2.putText(image, "Red: Hit (+1)", (start_x + 40, start_y + 18),
                   font, font_scale, self.TEXT_COLOR, thickness)

        # 藍色物件說明
        cv2.circle(image, (start_x + 15, start_y + line_height + 10), 12, self.COLOR_NOTE_BOMB, -1)
        cv2.putText(image, "Blue: Bomb (-2)", (start_x + 40, start_y + line_height + 18),
                   font, font_scale, self.TEXT_COLOR, thickness)

        # 金色物件說明
        cv2.circle(image, (start_x + 15, start_y + line_height * 2 + 10), 12, self.COLOR_NOTE_BONUS, -1)
        cv2.putText(image, "Gold: Bonus (+2)", (start_x + 40, start_y + line_height * 2 + 18),
                   font, font_scale, self.TEXT_COLOR, thickness)