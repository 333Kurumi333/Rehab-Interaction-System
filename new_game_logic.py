import math
import random

class GameEngine:
    """
    復健互動遊戲的邏輯引擎。
    管理物件生成、移動、狀態更新以及碰撞判定。
    """
    
    def __init__(self, width, height, arc_radius=350, zone_count=4, note_speed=3, hit_threshold=50):
        # --- 遊戲設定 ---
        self.width = width
        self.height = height
        self.score = 0
        self.notes = []             # 存放所有活動中的物件
        self.spawn_timer = 0        # 控制物件生成頻率的計時器

        # --- 介面/幾何參數 ---
        self.ARC_CENTER = (width // 2, height) # 半圓圓心設定在畫面底部中央
        self.ARC_RADIUS = arc_radius          # 復健區(半圓)的半徑
        self.ZONE_COUNT = zone_count          # 將半圓分成幾個區塊
        self.ZONE_ANGLE_WIDTH = 180 / zone_count # 每個區塊的角度寬度
        self.NOTE_SPEED = note_speed          # 物件移動速度 (像素/幀)
        self.HIT_THRESHOLD = hit_threshold    # 判定手部與物件的距離寬容度 (像素)
        self.LINE_HIT_TOLERANCE = 80          # 判定物件是否在半圓軌道上的寬容度 (像素) - 增加彈性
        self.NOTE_RADIUS = 20                 # 物件的繪製半徑
        
        # --- 狀態追蹤 ---
        # 用於避免持續接觸時一直得分
        self.last_hit_note_id = -1 
        self.next_note_id = 0 # 用於給每個 note 獨一無二的 ID

    def _spawn_note(self):
        """生成一個新的物件並加入到列表"""
        zone = random.randint(0, self.ZONE_COUNT - 1)
        
        # 計算該區塊的角度範圍
        start_angle = 180 - (zone * self.ZONE_ANGLE_WIDTH)
        end_angle = 180 - ((zone + 1) * self.ZONE_ANGLE_WIDTH)
        angle = random.uniform(end_angle + 10, start_angle - 10)
        
        # 初始位置半徑 (從外圍開始)
        initial_radius = self.ARC_RADIUS + 300 
        
        self.notes.append({
            'id': self.next_note_id,
            'zone_index': zone,
            'angle': angle,
            'current_radius': initial_radius,
            'active': True,
            'status': 'active' # 狀態：active, hit, miss
        })
        self.next_note_id += 1

    def _update_notes(self):
        """更新所有物件的位置和狀態"""
        notes_to_remove = []
        for note in self.notes:
            if not note['active']:
                notes_to_remove.append(note)
                continue
                
            # 移動：半徑縮小 (從外往內)
            note['current_radius'] -= self.NOTE_SPEED
            
            # 判斷是否錯過 (Miss)
            if note['current_radius'] < self.ARC_RADIUS - self.LINE_HIT_TOLERANCE:
                note['active'] = False
                note['status'] = 'miss'
                notes_to_remove.append(note)

        # 移除已處理或錯過的物件
        for note in notes_to_remove:
            if note in self.notes:
                self.notes.remove(note)

    def get_note_position(self, note):
        """根據物件的極坐標計算其笛卡爾坐標 (用於繪圖或碰撞判定)"""
        # 極坐標 (r, θ) 轉換為笛卡爾坐標 (x, y)
        rad_angle = math.radians(note['angle'])
        x = int(self.ARC_CENTER[0] + note['current_radius'] * math.cos(rad_angle))
        y = int(self.ARC_CENTER[1] - note['current_radius'] * math.sin(rad_angle)) # Y 軸方向相反
        return (x, y)

    def update_game_state(self, hand_pos, spawn_rate=60):
        """
        更新遊戲狀態，包含物件生成、移動和碰撞判定。
        這是主要的遊戲迴圈邏輯。

        參數:
        hand_pos (tuple | None): MediaPipe 偵測到的手部 (x, y) 坐標，若無則為 None。
        spawn_rate (int): 每隔多少幀生成一個物件 (例如 60 幀約 2 秒)。
        
        回傳: 無 (但會更新 self.score 和 self.notes)
        """
        
        # 1. 物件生成
        self.spawn_timer += 1
        if self.spawn_timer >= spawn_rate:
            self._spawn_note()
            self.spawn_timer = 0
            
        # 2. 物件移動
        self._update_notes()
        
        # 3. 碰撞判定與計分
        if hand_pos is None:
            self.last_hit_note_id = -1 # 確保手離開後可以重新計分
            return
            
        for note in self.notes:
            if not note['active'] or note['status'] == 'hit':
                continue
                
            # 計算物件與中心點的距離 (判斷是否在軌道上)
            note_x, note_y = self.get_note_position(note)
            
            # 判斷條件 A: 物件是否在目標軌道上 (時機點判定)
            distance_to_center = math.hypot(note_x - self.ARC_CENTER[0], note_y - self.ARC_CENTER[1])
            on_the_line = abs(distance_to_center - self.ARC_RADIUS) < self.LINE_HIT_TOLERANCE
            
            # 判斷條件 B: 手與物件的距離 (準確度判定)
            dist_hand_to_note = math.hypot(hand_pos[0] - note_x, hand_pos[1] - note_y)

            # 綜合判定：必須在線上 AND 手要碰到物件
            if on_the_line and dist_hand_to_note < (self.NOTE_RADIUS + self.HIT_THRESHOLD):
                
                # 確保同一個物件不會被連續觸碰兩次
                if note['id'] != self.last_hit_note_id:
                    self.score += 1
                    note['status'] = 'hit'
                    self.last_hit_note_id = note['id']
                    # 可以在這裡觸發視覺或音效回饋
                
    def get_notes_for_drawing(self):
        """回傳目前所有物件的繪圖資訊"""
        drawing_data = []
        for note in self.notes:
            pos = self.get_note_position(note)
            # 根據狀態設定顏色
            color = 'red'
            if note['status'] == 'hit':
                color = 'green'
            
            drawing_data.append({
                'pos': pos,
                'radius': self.NOTE_RADIUS,
                'status': note['status'],
                'color': color # 輸出顏色資訊給繪圖程式
            })
        return drawing_data

    def get_score(self):
        """回傳目前分數"""
        return self.score

    def get_arc_info(self):
        """回傳半圓的繪圖資訊，方便外部程式繪製 UI"""
        return {
            'center': self.ARC_CENTER,
            'radius': self.ARC_RADIUS,
            'zone_count': self.ZONE_COUNT,
            'zone_angle_width': self.ZONE_ANGLE_WIDTH
        }