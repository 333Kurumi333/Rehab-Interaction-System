import cv2
import math

class GameUI:
    def __init__(self):
        self.COLOR_ARC = (200, 200, 200)      
        self.COLOR_ZONE_LINE = (100, 100, 100) 
        self.COLOR_JUDGE_ZONE = (0, 255, 255) 
        
        self.COLOR_NOTE_ACTIVE = (0, 0, 255)  
        self.COLOR_NOTE_HIT = (0, 255, 0)     
        self.COLOR_NOTE_MISS = (128, 128, 128) 
        self.COLOR_NOTE_BONUS = (0, 215, 255) 
        self.TEXT_COLOR = (255, 255, 255)     

    # === 修改：新增 combo 參數 ===
    def draw_game_elements(self, image, arc_info, notes_data, score, accuracy=None, level=1, combo=0):
        self._draw_judge_zone(image, arc_info)
        self._draw_arc(image, arc_info)
        self._draw_zone_lines(image, arc_info)
        self._draw_notes(image, notes_data)
        self._draw_score(image, score, level)
        
        # === 新增：繪製 Combo ===
        if combo > 0:
            self._draw_combo(image, combo)

        if accuracy is not None:
            self._draw_accuracy(image, accuracy)
        if level >= 2:
            self._draw_legend(image)

    def _draw_combo(self, image, combo):
        """在畫面中央繪製 Combo 數"""
        height, width = image.shape[:2]
        center_x, center_y = int(width / 2), int(height / 2)
        
        # 繪製 "COMBO" 文字
        cv2.putText(image, "COMBO", (center_x - 80, center_y - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # 繪製數字 (根據連擊數變色，越打越High)
        color = (0, 255, 255) # 預設黃色
        if combo > 10: color = (0, 200, 255) # 橘黃
        if combo > 30: color = (0, 100, 255) # 橘紅
        
        # 數字置中計算
        text = str(combo)
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 3, 5)[0]
        text_x = center_x - int(text_size[0] / 2)
        
        cv2.putText(image, text, (text_x, center_y + 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 3, color, 5)

    def _draw_judge_zone(self, image, arc_info):
        center = arc_info['center']
        radius = arc_info['radius']
        tolerance = arc_info.get('hit_tolerance', 80)

        overlay = image.copy()
        cv2.ellipse(overlay, center, (radius, radius), 0, 180, 360, 
                    self.COLOR_JUDGE_ZONE, thickness=tolerance * 2)
        cv2.addWeighted(overlay, 0.2, image, 0.8, 0, image)

    def _draw_arc(self, image, arc_info):
        center = arc_info['center']
        radius = arc_info['radius']
        cv2.ellipse(image, center, (radius, radius), 0, 180, 360, (255, 255, 255), 2)

    def _draw_zone_lines(self, image, arc_info):
        center = arc_info['center']
        radius = arc_info['radius']
        zone_count = arc_info['zone_count']
        zone_angle_width = arc_info['zone_angle_width']

        for i in range(1, zone_count):
            angle = 180 - (i * zone_angle_width)
            rad_angle = math.radians(angle)
            inner_r, outer_r = radius - 80, radius + 80
            start_x = int(center[0] + inner_r * math.cos(rad_angle))
            start_y = int(center[1] - inner_r * math.sin(rad_angle))
            end_x = int(center[0] + outer_r * math.cos(rad_angle))
            end_y = int(center[1] - outer_r * math.sin(rad_angle))
            cv2.line(image, (start_x, start_y), (end_x, end_y), self.COLOR_ZONE_LINE, 2)

    def _draw_notes(self, image, notes_data):
        for note in notes_data:
            pos = note['pos']
            radius = note['radius']
            status = note['status']
            note_type = note.get('type', 'normal')

            if status == 'hit': color = self.COLOR_NOTE_HIT
            elif status == 'miss': color = self.COLOR_NOTE_MISS
            elif note_type == 'bonus': color = self.COLOR_NOTE_BONUS
            else: color = self.COLOR_NOTE_ACTIVE

            cv2.circle(image, pos, radius, color, -1)
            cv2.circle(image, pos, radius, (255,255,255), 2)

            if status == 'hit':
                text = "+2!" if note_type == 'bonus' else "HIT!"
                c = self.COLOR_NOTE_BONUS if note_type == 'bonus' else self.COLOR_NOTE_HIT
                cv2.putText(image, text, (pos[0]-30, pos[1]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, c, 2)

    def _draw_score(self, image, score, level=1):
        cv2.putText(image, f"Level {level}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 200, 255), 3)
        cv2.putText(image, f"Score: {score}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.TEXT_COLOR, 3)

    def _draw_accuracy(self, image, accuracy):
        height, width = image.shape[:2]
        text = f"Accuracy: {accuracy:.1f}%"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
        cv2.putText(image, text, (width - text_size[0] - 20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.TEXT_COLOR, 3)

    def _draw_legend(self, image):
        """繪製物件說明（移除藍球）"""
        height, width = image.shape[:2]
        start_x = 20
        start_y = height - 100 # 位置稍微往下移，因為少了一行
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # 紅色物件
        cv2.circle(image, (start_x + 15, start_y + 10), 12, self.COLOR_NOTE_ACTIVE, -1)
        cv2.putText(image, "Red: Hit (+1)", (start_x + 40, start_y + 18), font, 0.7, self.TEXT_COLOR, 2)

        # 金色物件
        cv2.circle(image, (start_x + 15, start_y + 45), 12, self.COLOR_NOTE_BONUS, -1)
        cv2.putText(image, "Gold: Bonus (+2)", (start_x + 40, start_y + 53), font, 0.7, self.TEXT_COLOR, 2)