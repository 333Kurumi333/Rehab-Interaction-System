import cv2
import math
import numpy as np
import time

class GameUI:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        # === 色彩設定 ===
        self.COLOR_BG_PANEL = (50, 50, 50)     
        self.COLOR_ZONE_LINE = (200, 200, 200) 
        self.COLOR_JUDGE_ZONE = (0, 255, 255)  
        self.COLOR_NOTE_NORMAL = (0, 0, 255)   
        self.COLOR_NOTE_BONUS = (0, 215, 255)  
        self.COLOR_NOTE_HIT = (0, 255, 0)      
        self.COLOR_NOTE_MISS = (100, 100, 100) 
        self.COLOR_MENU_BOX = (255, 200, 100)       
        self.COLOR_MENU_BOX_HOVER = (0, 165, 255)   
        self.COLOR_MENU_TEXT = (50, 50, 50)         
        
        self.start_time = time.time()
        self.mask = None
        self.mask_inv = None
        self._init_mask(width, height)

    def _init_mask(self, width, height):
        self.mask = np.zeros((height, width), dtype=np.uint8)
        center = (width // 2, height)
        radius = int(width * 0.45) 
        cv2.circle(self.mask, center, radius, 255, -1)
        self.mask_inv = cv2.bitwise_not(self.mask)
        self.mask = cv2.cvtColor(self.mask, cv2.COLOR_GRAY2BGR)
        self.mask_inv = cv2.cvtColor(self.mask_inv, cv2.COLOR_GRAY2BGR)

    # === [新增] FPS 繪製 ===
    def draw_fps(self, image, fps):
        # 顯示在左下角
        cv2.putText(image, f"FPS: {int(fps)}", (20, self.height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    def draw_menu(self, image, song_list, hover_index, hover_progress, fps=0):
        h, w = image.shape[:2]
        cv2.putText(image, "Select Song", (50, 100), cv2.FONT_HERSHEY_DUPLEX, 2.0, (255, 255, 255), 3)
        cv2.putText(image, "Hover 3 seconds to start", (55, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)

        start_y = 250
        box_height = 120
        gap = 40
        box_width = int(w * 0.6)
        box_x = int((w - box_width) / 2)

        box_regions = []
        for i, song in enumerate(song_list):
            y = start_y + i * (box_height + gap)
            is_hover = (i == hover_index)
            color = self.COLOR_MENU_BOX_HOVER if is_hover else self.COLOR_MENU_BOX
            cv2.rectangle(image, (box_x, y), (box_x + box_width, y + box_height), color, -1)
            cv2.rectangle(image, (box_x, y), (box_x + box_width, y + box_height), (255, 255, 255), 3)
            if is_hover and hover_progress > 0:
                progress_w = int(box_width * hover_progress)
                cv2.rectangle(image, (box_x, y), (box_x + progress_w, y + box_height), (0, 255, 0), -1)
            
            font_scale = 1.2
            text = f"{i+1}. {song['name']} ({song['bpm']} BPM)"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]
            text_x = box_x + 30
            text_y = y + int((box_height + text_size[1]) / 2)
            cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, self.COLOR_MENU_TEXT, 3, cv2.LINE_AA)
            box_regions.append((box_x, y, box_x + box_width, y + box_height))
        
        self.draw_fps(image, fps)
        return box_regions

    def draw_result_panel(self, image, stats, hover_progress, fps=0):
        h, w = image.shape[:2]
        center_x = w // 2
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.85, image, 0.15, 0, image)
        
        self._draw_centered_text(image, "GAME OVER", center_x, 150, 3.0, (0, 255, 255))
        start_y = 300
        gap = 80
        items = [("TOTAL BALLS", stats['total']), ("HIT", stats['hit']), ("MISS", stats['miss']), ("MAX COMBO", stats['combo']), ("SCORE", stats['score'])]
        for i, (label, value) in enumerate(items):
            y = start_y + i * gap
            color = (255, 255, 255)
            if label == "SCORE": color = (0, 215, 255)
            if label == "MISS":  color = (100, 100, 255)
            self._draw_centered_text(image, f"{label}: {value}", center_x, y, 1.5, color)
        
        btn_w, btn_h = 400, 100
        btn_x = center_x - btn_w // 2
        btn_y = h - 200
        color = self.COLOR_MENU_BOX_HOVER if hover_progress > 0 else self.COLOR_MENU_BOX
        cv2.rectangle(image, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), color, -1)
        cv2.rectangle(image, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), (255, 255, 255), 3)
        if hover_progress > 0:
            prog_w = int(btn_w * hover_progress)
            cv2.rectangle(image, (btn_x, btn_y), (btn_x + prog_w, btn_y + btn_h), (0, 255, 0), -1)
        text = "MAIN MENU"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
        text_x = btn_x + (btn_w - text_size[0]) // 2
        text_y = btn_y + (btn_h + text_size[1]) // 2
        cv2.putText(image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1.5, self.COLOR_MENU_TEXT, 3, cv2.LINE_AA)
        
        self.draw_fps(image, fps)
        return (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h)

    def _draw_centered_text(self, image, text, cx, cy, scale, color):
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 3)[0]
        tx = cx - text_size[0] // 2
        self._draw_shadow_text(image, text, (tx, cy), scale, color, thickness=3)

    # === [修改] 接收 song_name 和 fps ===
    def draw_game_elements(self, image, arc_info, notes_data, score, accuracy=None, combo=0, song_name="", fps=0, time_progress=0):
        elapsed = time.time() - self.start_time
        pulse = (math.sin(elapsed * 3) + 1) / 2 
        self._draw_judge_zone(image, arc_info, pulse)
        self._draw_track_lines(image, arc_info)
        self._draw_notes(image, notes_data, pulse)
        
        # 傳遞 time_progress 給 dashboard
        self._draw_dashboard(image, score, accuracy, song_name, time_progress)
        
        if combo > 1:
            self._draw_combo(image, combo, pulse)
            
        self.draw_fps(image, fps)

    def _draw_judge_zone(self, image, arc_info, pulse):
        center = arc_info['center']
        radius = arc_info['radius']
        base_tolerance = arc_info.get('hit_tolerance', 80)
        dynamic_width = int(base_tolerance + (pulse * 5))
        overlay = image.copy()
        cv2.ellipse(overlay, center, (radius, radius), 0, 180, 360, self.COLOR_JUDGE_ZONE, thickness=dynamic_width * 2)
        alpha = 0.2 + (pulse * 0.15)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
        cv2.ellipse(image, center, (radius - dynamic_width, radius - dynamic_width), 0, 180, 360, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.ellipse(image, center, (radius + dynamic_width, radius + dynamic_width), 0, 180, 360, (255, 255, 0), 2, cv2.LINE_AA)

    def _draw_track_lines(self, image, arc_info):
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
        for note in notes_data:
            pos = note['pos']
            radius = int(note['radius'])
            status = note['status']
            note_type = note.get('type', 'normal')
            if status == 'hit': 
                color = self.COLOR_NOTE_HIT
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
            cv2.circle(image, (pos[0]+3, pos[1]+3), radius, (0,0,0), -1, cv2.LINE_AA)
            cv2.circle(image, pos, radius, color, -1, cv2.LINE_AA)
            cv2.circle(image, pos, radius, (255, 255, 255), 2, cv2.LINE_AA)
            if status == 'hit':
                text = "+2" if note_type == 'bonus' else "Good!"
                self._draw_shadow_text(image, text, (pos[0]-60, pos[1]-60), 1.0, (255, 255, 255), thickness=2)

    def _draw_dashboard(self, image, score, accuracy, song_name="", time_progress=0):
        h, w = image.shape[:2]
        panel_height = 100
        cv2.rectangle(image, (0, 0), (w, panel_height), self.COLOR_BG_PANEL, -1)
        
        # 時間進度條（取代命中率進度條）
        bar_width = int((w - 40) * min(time_progress, 1.0))
        bar_color = (0, 200, 255)  # 橙黃色
        cv2.rectangle(image, (20, panel_height - 10), (w-20, panel_height), (30, 30, 30), -1)
        cv2.rectangle(image, (20, panel_height - 10), (20 + bar_width, panel_height), bar_color, -1)
        
        # === Score 在左側 ===
        score_text = f"SCORE: {score}"
        self._draw_shadow_text(image, score_text, (20, 60), 1.5, (255, 255, 255), thickness=3)
        
        # === 歌名在中間 ===
        if song_name:
            text_size = cv2.getTextSize(song_name, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            center_x = (w - text_size[0]) // 2
            self._draw_shadow_text(image, song_name, (center_x, 60), 1.2, (255, 255, 255), thickness=3)

        # === 命中率在右側 ===
        if accuracy is not None:
            acc_text = f"{accuracy:.1f}%"
            acc_color = (0, 255, 0) if accuracy > 80 else (0, 0, 255)
            text_size = cv2.getTextSize(acc_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            self._draw_shadow_text(image, acc_text, (w - text_size[0] - 30, 60), 1.2, acc_color, thickness=3)

    def _draw_combo(self, image, combo, pulse):
        h, w = image.shape[:2]
        center_x, center_y = w // 2, h // 2
        scale = 2.0 + (min(combo, 50) / 50.0) + (pulse * 0.2) 
        color = (0, 255, 255) 
        if combo >= 10: color = (0, 165, 255) 
        if combo >= 30: color = (0, 0, 255)   
        self._draw_shadow_text(image, "COMBO", (center_x - 100, center_y - 20), 1.0, (255, 255, 255), thickness=3)
        text = str(combo)
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 5)[0]
        text_x = center_x - (text_size[0] // 2)
        text_y = center_y + 100
        self._draw_shadow_text(image, text, (text_x, text_y), scale, color, thickness=5)

    def _draw_shadow_text(self, image, text, pos, scale, color, thickness=2):
        cv2.putText(image, text, (pos[0]+3, pos[1]+3), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness, cv2.LINE_AA)
        cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)