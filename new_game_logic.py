import math
import random

class GameEngine:
    """
    復健互動遊戲的邏輯引擎。
    管理物件生成、移動、狀態更新以及碰撞判定。
    """
    
    def __init__(self, width, height, arc_radius=350, zone_count=4, note_speed=3, hit_threshold=50, level=1, notes_per_beat=1):
        # --- 遊戲設定 ---
        self.width = width
        self.height = height
        self.score = 0
        self.notes = []             # 存放所有活動中的物件
        self.spawn_timer = 0        # 控制物件生成頻率的計時器
        self.level = level          # 目前關卡
        self.notes_per_beat = notes_per_beat  # 每個節拍生成幾個物件

        # --- 準確率統計 ---
        self.total_notes = 0        # 總共出現的物件數
        self.hit_notes = 0          # 成功擊中的物件數
        self.miss_notes = 0         # 錯過的物件數

        # --- 介面/幾何參數 ---
        self.ARC_CENTER = (width // 2, height) # 半圓圓心設定在畫面底部中央
        self.ARC_RADIUS = arc_radius          # 復健區(半圓)的半徑
        self.ZONE_COUNT = zone_count          # 將半圓分成幾個區塊
        self.ZONE_ANGLE_WIDTH = 180 / zone_count # 每個區塊的角度寬度
        self.NOTE_SPEED = note_speed          # 物件移動速度 (像素/幀)
        self.HIT_THRESHOLD = hit_threshold    # 判定手部與物件的距離寬容度 (像素)
        self.LINE_HIT_TOLERANCE = 120         # 判定物件是否在半圓軌道上的寬容度 (80 -> 120，增加 50%)
        self.NOTE_RADIUS = 30                 # 物件的繪製半徑 (20 -> 30，增加 50%)

        # --- 狀態追蹤 ---
        # 用於避免持續接觸時一直得分
        self.last_hit_note_id = -1
        self.next_note_id = 0 # 用於給每個 note 獨一無二的 ID
        self.last_spawn_zones = []  # 記錄最近生成的區域，避免重疊

    def _get_available_zones(self, count):
        """取得可用的區域，避免與最近生成的物件重疊"""
        all_zones = list(range(self.ZONE_COUNT))

        # 過濾掉最近使用的區域和相鄰區域
        available_zones = []
        for zone in all_zones:
            # 檢查這個區域和相鄰區域是否被占用
            is_available = True
            for used_zone in self.last_spawn_zones:
                # 如果距離小於2個區域，視為太近
                if abs(zone - used_zone) < 2:
                    is_available = False
                    break
            if is_available:
                available_zones.append(zone)

        # 如果沒有可用區域，清空記錄重新開始
        if len(available_zones) < count:
            self.last_spawn_zones = []
            available_zones = all_zones

        # 隨機選擇 count 個不重複的區域
        selected = random.sample(available_zones, min(count, len(available_zones)))
        return selected

    def _spawn_note(self, zone=None):
        """生成一個新的物件並加入到列表"""
        if zone is None:
            zone = random.randint(0, self.ZONE_COUNT - 1)

        # 計算該區塊的角度範圍
        start_angle = 180 - (zone * self.ZONE_ANGLE_WIDTH)
        end_angle = 180 - ((zone + 1) * self.ZONE_ANGLE_WIDTH)
        angle = random.uniform(end_angle + 10, start_angle - 10)

        # 初始位置半徑 (從外圍開始)
        initial_radius = self.ARC_RADIUS + 300

        # 決定物件類型（第二關才有特殊物件）
        note_type = 'normal'  # 預設為普通物件
        if self.level >= 2:
            # 第二關：80% 正常（紅色），15% 炸彈（藍色），5% 加分（金色）
            rand = random.random()
            if rand < 0.80:
                note_type = 'normal'   # 紅色 - 正常擊中
            elif rand < 0.95:
                note_type = 'bomb'     # 藍色 - 不能碰
            else:
                note_type = 'bonus'    # 金色 - 雙倍分數

        self.notes.append({
            'id': self.next_note_id,
            'zone_index': zone,
            'angle': angle,
            'current_radius': initial_radius,
            'active': True,
            'status': 'active',  # 狀態：active, hit, miss
            'type': note_type    # 物件類型：normal, bomb, bonus
        })
        self.next_note_id += 1
        self.total_notes += 1  # 增加總物件數

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
                if note['status'] != 'hit':  # 只有沒被擊中的才算 miss
                    note['status'] = 'miss'
                    self.miss_notes += 1
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

    def update_game_state(self, hand_pos, spawn_rate=60, music_controller=None):
        """
        更新遊戲狀態，包含物件生成、移動和碰撞判定。
        這是主要的遊戲迴圈邏輯。

        參數:
        hand_pos (tuple | None): MediaPipe 偵測到的手部 (x, y) 坐標，若無則為 None。
        spawn_rate (int): 每隔多少幀生成一個物件 (例如 60 幀約 2 秒)。
        music_controller (MusicController | None): 音樂控制器，用於節奏同步。

        回傳: 無 (但會更新 self.score 和 self.notes)
        """

        # 1. 物件生成
        # 如果有音樂控制器，根據節奏生成；否則使用原本的計時器
        if music_controller is not None:
            if music_controller.should_spawn_note():
                # 取得不重疊的區域
                zones = self._get_available_zones(self.notes_per_beat)
                # 在每個區域生成物件
                for zone in zones:
                    self._spawn_note(zone)
                # 記錄這次使用的區域
                self.last_spawn_zones = zones
        else:
            self.spawn_timer += 1
            if self.spawn_timer >= spawn_rate:
                # 取得不重疊的區域
                zones = self._get_available_zones(self.notes_per_beat)
                # 在每個區域生成物件
                for zone in zones:
                    self._spawn_note(zone)
                # 記錄這次使用的區域
                self.last_spawn_zones = zones
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
                    note_type = note.get('type', 'normal')

                    if note_type == 'normal':
                        # 紅色物件：正常擊中 +1 分
                        self.score += 1
                        note['status'] = 'hit'
                        self.hit_notes += 1
                    elif note_type == 'bonus':
                        # 金色物件：雙倍分數 +2 分
                        self.score += 2
                        note['status'] = 'hit'
                        self.hit_notes += 1
                    elif note_type == 'bomb':
                        # 藍色物件：不能碰，扣 2 分
                        self.score = max(0, self.score - 2)  # 分數不會小於 0
                        note['status'] = 'bomb_hit'  # 特殊狀態表示碰到炸彈

                    self.last_hit_note_id = note['id']
                    # 可以在這裡觸發視覺或音效回饋
                
    def get_notes_for_drawing(self):
        """回傳目前所有物件的繪圖資訊"""
        drawing_data = []
        for note in self.notes:
            pos = self.get_note_position(note)
            note_type = note.get('type', 'normal')

            # 根據物件類型設定顏色
            if note['status'] == 'hit':
                color = 'green'  # 擊中後顯示綠色
            elif note['status'] == 'bomb_hit':
                color = 'gray'   # 碰到炸彈顯示灰色
            elif note_type == 'normal':
                color = 'red'    # 紅色 - 正常物件
            elif note_type == 'bomb':
                color = 'blue'   # 藍色 - 炸彈（不能碰）
            elif note_type == 'bonus':
                color = 'gold'   # 金色 - 加分物件
            else:
                color = 'red'    # 預設紅色

            drawing_data.append({
                'pos': pos,
                'radius': self.NOTE_RADIUS,
                'status': note['status'],
                'type': note_type,
                'color': color # 輸出顏色資訊給繪圖程式
            })
        return drawing_data

    def get_score(self):
        """回傳目前分數"""
        return self.score

    def get_accuracy(self):
        """回傳準確率（百分比）"""
        if self.total_notes == 0:
            return 0.0
        return (self.hit_notes / self.total_notes) * 100

    def get_arc_info(self):
        """回傳半圓的繪圖資訊，方便外部程式繪製 UI"""
        return {
            'center': self.ARC_CENTER,
            'radius': self.ARC_RADIUS,
            'zone_count': self.ZONE_COUNT,
            'zone_angle_width': self.ZONE_ANGLE_WIDTH
        }