import cv2
import math
import numpy as np
import time

class GameUI:
    def __init__(self):
        # === 1. 色彩設定 (BGR 格式) ===
        self.COLOR_BG_PANEL = (50, 50, 50)     # 資訊列背景
        self.COLOR_ZONE_LINE = (200, 200, 200) # 軌道線
        self.COLOR_JUDGE_ZONE = (0, 255, 255)  # 判定區 (黃)
        
        # 物件顏色
        self.COLOR_NOTE_NORMAL = (0, 0, 255)   # 紅色
        self.COLOR_NOTE_BONUS = (0, 215, 255)  # 金色
        self.COLOR_NOTE_HIT = (0, 255, 0)      # 綠色
        self.COLOR_NOTE_MISS = (100, 100, 100) # 灰色
        
        # 用於動畫計算的時間戳記
        self.start_time = time.time()

    def draw_game_elements(self, image, arc_info, notes_data, score, accuracy=None, level=1, combo=0):
        """ 主繪圖函數 """
        # 計算全域動畫參數 (例如呼吸頻率)
        elapsed = time.time() - self.start_time
        pulse = (math.sin(elapsed * 3) + 1) / 2  # 0.0 ~ 1.0 的波動值
        
        # A. 繪製判定區 (加入呼吸效果)
        self._draw_judge_zone(image, arc_info, pulse)
        
        # B. 繪製軌道線
        self._draw_track_lines(image, arc_info)
        
        # C. 繪製掉落物件 (加入擊中震波)
        self._draw_notes(image, notes_data, pulse)
        
        # D. 繪製資訊看板 (加入能量條與陰影)
        self._draw_dashboard(image, score, accuracy, level)
        
        # E. 繪製 Combo (加入縮放動畫)
        if combo > 1:
            self._draw_combo(image, combo, pulse)

    def _draw_judge_zone(self, image, arc_info, pulse):
        """ 呼吸燈效果的判定區 """
        center = arc_info['center']
        radius = arc_info['radius']
        base_tolerance = arc_info.get('hit_tolerance', 80)
        
        # 讓判定區寬度微微縮放 (呼吸感)
        dynamic_width = int(base_tolerance + (pulse * 5))
        
        # 1. 半透明光暈
        overlay = image.copy()
        cv2.ellipse(overlay, center, (radius, radius), 0, 180, 360, 
                    self.COLOR_JUDGE_ZONE, thickness=dynamic_width * 2)
        
        # 透明度隨 pulse 變化 (忽明忽暗)
        alpha = 0.2 + (pulse * 0.15)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
        
        # 2. 邊框線條
        cv2.ellipse(image, center, (radius - dynamic_width, radius - dynamic_width), 0, 180, 360, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.ellipse(image, center, (radius + dynamic_width, radius + dynamic_width), 0, 180, 360, (255, 255, 0), 2, cv2.LINE_AA)

    def _draw_track_lines(self, image, arc_info):
        """ 繪製軌道線 """
        center = arc_info['center']
        radius = arc_info['radius']
        zone_count = arc_info['zone_count']
        zone_angle_width = arc_info['zone_angle_width']
        
        cv2.ellipse(image, center, (radius, radius), 0, 180, 360, (255, 255, 255), 2, cv2.LINE_AA)

        for i in range(1, zone_count):
            angle = 180 - (i * zone_angle_width)
            rad_angle = math.radians(angle)
            
            inner_r, outer_r = radius - 100, radius + 100
            start_point = (int(center[0] + inner_r * math.cos(rad_angle)), int(center[1] - inner_r * math.sin(rad_angle)))
            end_point = (int(center[0] + outer_r * math.cos(rad_angle)), int(center[1] - outer_r * math.sin(rad_angle)))
            
            cv2.line(image, start_point, end_point, self.COLOR_ZONE_LINE, 2, cv2.LINE_AA)

    def _draw_notes(self, image, notes_data, pulse):
        """ 繪製物件與擊中特效 """
        for note in notes_data:
            pos = note['pos']
            radius = int(note['radius'])
            status = note['status']
            note_type = note.get('type', 'normal')

            if status == 'hit': 
                color = self.COLOR_NOTE_HIT
                # === 特效：擊中震波 (Ripple) ===
                # 畫兩個擴散的圈圈
                ripple_r1 = radius + int(pulse * 10) + 5
                ripple_r2 = radius + int(pulse * 20) + 15
                cv2.circle(image, pos, ripple_r1, color, 2, cv2.LINE_AA)
                cv2.circle(image, pos, ripple_r2, (255, 255, 255), 1, cv2.LINE_AA)
                
            elif status == 'miss': 
                color = self.COLOR_NOTE_MISS
            elif note_type == 'bonus': 
                color = self.COLOR_NOTE_BONUS
            else: 
                color = self.COLOR_NOTE_NORMAL

            # 畫球體陰影 (立體感)
            cv2.circle(image, (pos[0]+3, pos[1]+3), radius, (0,0,0), -1, cv2.LINE_AA)
            # 畫球體本體
            cv2.circle(image, pos, radius, color, -1, cv2.LINE_AA)
            cv2.circle(image, pos, radius, (255, 255, 255), 2, cv2.LINE_AA)

            # 擊中文字特效
            if status == 'hit':
                text = "+2" if note_type == 'bonus' else "Good!"
                self._draw_shadow_text(image, text, (pos[0]-40, pos[1]-40), 1.0, (255, 255, 255))

    def _draw_dashboard(self, image, score, accuracy, level):
        """ 繪製資訊看板 (含能量條) """
        h, w = image.shape[:2]
        
        # 1. 資訊面板背景
        cv2.rectangle(image, (0, 0), (w, 100), self.COLOR_BG_PANEL, -1)
        
        # 2. 能量條 (Energy Bar) - 根據準確率顯示
        if accuracy is not None:
            bar_width = int((w - 60) * (accuracy / 100.0))
            bar_color = (0, 255, 0) if accuracy > 80 else (0, 165, 255)
            if accuracy < 50: bar_color = (0, 0, 255)
            
            # 畫能量條底槽
            cv2.rectangle(image, (30, 90), (w-30, 98), (30, 30, 30), -1)
            # 畫能量條本體
            cv2.rectangle(image, (30, 90), (30 + bar_width, 98), bar_color, -1)

        # 3. 文字資訊 (使用陰影函數)
        self._draw_shadow_text(image, f"LEVEL {level}", (30, 60), 1.2, (255, 255, 0))
        
        # 分數置中
        score_text = f"SCORE: {score}"
        text_size = cv2.getTextSize(score_text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
        center_x = (w - text_size[0]) // 2
        self._draw_shadow_text(image, score_text, (center_x, 60), 1.5, (255, 255, 255))

        if accuracy is not None:
            acc_text = f"{accuracy:.1f}%"
            acc_color = (0, 255, 0) if accuracy > 80 else (0, 0, 255)
            text_size = cv2.getTextSize(acc_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            self._draw_shadow_text(image, acc_text, (w - text_size[0] - 30, 60), 1.2, acc_color)

    def _draw_combo(self, image, combo, pulse):
        """ 繪製動態 Combo """
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Combo 字體隨 pulse 縮放 (心跳感)
        scale = 2.0 + (min(combo, 50) / 50.0) + (pulse * 0.2)
        
        color = (0, 255, 255) 
        if combo >= 10: color = (0, 165, 255) 
        if combo >= 30: color = (0, 0, 255)   

        # COMBO 標題
        self._draw_shadow_text(image, "COMBO", (center_x - 100, center_y - 20), 1.0, (255, 255, 255), thickness=2)
        
        # COMBO 數字
        text = str(combo)
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 5)[0]
        text_x = center_x - (text_size[0] // 2)
        text_y = center_y + 100
        
        self._draw_shadow_text(image, text, (text_x, text_y), scale, color, thickness=5)

    def _draw_shadow_text(self, image, text, pos, scale, color, thickness=3):
        """ 輔助函數：畫出帶有陰影的文字 """
        # 先畫黑色的陰影 (位置偏移 +3)
        cv2.putText(image, text, (pos[0]+3, pos[1]+3), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness, cv2.LINE_AA)
        # 再畫彩色的本體
        cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)