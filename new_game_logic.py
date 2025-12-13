import math
import random

class GameEngine:
    def __init__(self, width, height, arc_radius=350, zone_count=4, note_speed=3, hit_threshold=50, level=1, notes_per_beat=1):
        # ... (前面的設定保持不變) ...
        self.width = width
        self.height = height
        self.score = 0
        self.combo = 0              # <--- 新增：連擊數
        self.max_combo = 0          # <--- 新增：最大連擊紀錄
        self.notes = []             
        self.spawn_timer = 0        
        self.level = level          
        self.notes_per_beat = notes_per_beat  

        self.total_notes = 0        
        self.hit_notes = 0          
        self.miss_notes = 0         

        self.ARC_CENTER = (width // 2, height) 
        self.ARC_RADIUS = arc_radius          
        self.ZONE_COUNT = zone_count          
        self.ZONE_ANGLE_WIDTH = 180 / zone_count 
        self.NOTE_SPEED = note_speed          
        self.HIT_THRESHOLD = 70               
        self.LINE_HIT_TOLERANCE = 80          
        self.NOTE_RADIUS = 30                 

        self.last_hit_note_id = -1
        self.next_note_id = 0 
        self.last_spawn_zones = []  

    def _get_available_zones(self, count):
        # ... (這部分邏輯不變，省略以節省版面) ...
        all_zones = list(range(self.ZONE_COUNT))
        available_zones = []
        for zone in all_zones:
            is_available = True
            for used_zone in self.last_spawn_zones:
                if abs(zone - used_zone) < 2:
                    is_available = False
                    break
            if is_available:
                available_zones.append(zone)
        if len(available_zones) < count:
            self.last_spawn_zones = []
            available_zones = all_zones
        return random.sample(available_zones, min(count, len(available_zones)))

    def _spawn_note(self, zone=None):
        if zone is None:
            zone = random.randint(0, self.ZONE_COUNT - 1)

        start_angle = 180 - (zone * self.ZONE_ANGLE_WIDTH)
        end_angle = 180 - ((zone + 1) * self.ZONE_ANGLE_WIDTH)
        angle = random.uniform(end_angle + 10, start_angle - 10)

        initial_radius = 50 

        # === 修改重點：移除炸彈，只保留正常與加分 ===
        note_type = 'normal'
        if self.level >= 2:
            rand = random.random()
            if rand < 0.90:       # 90% 機率一般物件
                note_type = 'normal'
            else:                 # 10% 機率加分物件 (原本是 5%加分 15%炸彈)
                note_type = 'bonus'
            # 炸彈 logic 已刪除

        self.notes.append({
            'id': self.next_note_id,
            'zone_index': zone,
            'angle': angle,
            'current_radius': initial_radius,
            'active': True,
            'status': 'active',
            'type': note_type
        })
        self.next_note_id += 1
        self.total_notes += 1

    def _update_notes(self):
        notes_to_remove = []
        for note in self.notes:
            if not note['active']:
                notes_to_remove.append(note)
                continue
                
            note['current_radius'] += self.NOTE_SPEED
            
            # Miss 判定
            if note['current_radius'] > self.ARC_RADIUS + self.LINE_HIT_TOLERANCE:
                note['active'] = False
                if note['status'] != 'hit':
                    note['status'] = 'miss'
                    self.miss_notes += 1
                    self.combo = 0  # <--- 修改重點：漏接時 Combo 歸零
                notes_to_remove.append(note)

        for note in notes_to_remove:
            if note in self.notes:
                self.notes.remove(note)

    def get_note_position(self, note):
        # ... (邏輯不變) ...
        rad_angle = math.radians(note['angle'])
        x = int(self.ARC_CENTER[0] + note['current_radius'] * math.cos(rad_angle))
        y = int(self.ARC_CENTER[1] - note['current_radius'] * math.sin(rad_angle))
        return (x, y)

    def update_game_state(self, hand_pos, spawn_rate=60, music_controller=None):
        # 1. 生成 (不變)
        if music_controller is not None:
            if music_controller.should_spawn_note():
                zones = self._get_available_zones(self.notes_per_beat)
                for zone in zones: self._spawn_note(zone)
                self.last_spawn_zones = zones
        else:
            self.spawn_timer += 1
            if self.spawn_timer >= spawn_rate:
                zones = self._get_available_zones(self.notes_per_beat)
                for zone in zones: self._spawn_note(zone)
                self.last_spawn_zones = zones
                self.spawn_timer = 0

        # 2. 移動 (不變)
        self._update_notes()
        
        # 3. 碰撞 (移除扣分邏輯，加入 Combo)
        if hand_pos is None:
            self.last_hit_note_id = -1
            return
            
        for note in self.notes:
            if not note['active'] or note['status'] == 'hit':
                continue
                
            note_x, note_y = self.get_note_position(note)
            
            # 判定邏輯 (維持嚴格判定)
            dist_note_center = math.hypot(note_x - self.ARC_CENTER[0], note_y - self.ARC_CENTER[1])
            note_in_hit_zone = abs(dist_note_center - self.ARC_RADIUS) < self.LINE_HIT_TOLERANCE

            dist_hand_note = math.hypot(hand_pos[0] - note_x, hand_pos[1] - note_y)
            hand_touched_note = dist_hand_note < (self.NOTE_RADIUS + self.HIT_THRESHOLD)

            dist_hand_center = math.hypot(hand_pos[0] - self.ARC_CENTER[0], hand_pos[1] - self.ARC_CENTER[1])
            hand_on_line = abs(dist_hand_center - self.ARC_RADIUS) < self.LINE_HIT_TOLERANCE

            if note_in_hit_zone and hand_touched_note and hand_on_line:
                if note['id'] != self.last_hit_note_id:
                    note_type = note.get('type', 'normal')

                    if note_type == 'normal':
                        self.score += 1
                    elif note_type == 'bonus':
                        self.score += 2
                    
                    # === 修改重點：命中後 Combo 增加 ===
                    note['status'] = 'hit'
                    self.hit_notes += 1
                    self.combo += 1
                    if self.combo > self.max_combo:
                        self.max_combo = self.combo
                    
                    self.last_hit_note_id = note['id']
                
    def get_notes_for_drawing(self):
        # ... (稍微清理一下顏色邏輯，移除炸彈) ...
        drawing_data = []
        for note in self.notes:
            pos = self.get_note_position(note)
            note_type = note.get('type', 'normal')
            
            if note['status'] == 'hit': color = 'green'
            elif note_type == 'normal': color = 'red'
            elif note_type == 'bonus': color = 'gold'
            else: color = 'red'

            drawing_data.append({
                'pos': pos,
                'radius': self.NOTE_RADIUS,
                'status': note['status'],
                'type': note_type,
                'color': color
            })
        return drawing_data

    # ... (其他 getter) ...
    def get_score(self): return self.score
    def get_accuracy(self): 
        if self.total_notes == 0: return 0.0
        return (self.hit_notes / self.total_notes) * 100
    def get_arc_info(self):
        return {
            'center': self.ARC_CENTER,
            'radius': self.ARC_RADIUS,
            'zone_count': self.ZONE_COUNT,
            'zone_angle_width': self.ZONE_ANGLE_WIDTH,
            'hit_tolerance': self.LINE_HIT_TOLERANCE
        }
    
    # === 新增 Getter ===
    def get_combo(self):
        return self.combo