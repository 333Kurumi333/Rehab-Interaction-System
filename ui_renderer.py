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
        # 遮罩半徑 = arc_radius + hitbox 容差，確保背景影片剛好在 hitbox 外圈開始
        arc_radius = int(width * 0.4)
        hit_tolerance = 80
        radius = arc_radius + hit_tolerance
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

    def _draw_shadow_text(self, image, text, pos, scale, color, thickness=2):
        cv2.putText(image, text, (pos[0]+3, pos[1]+3), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness, cv2.LINE_AA)
        cv2.putText(image, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)