import math
import random
import os
import ast

class GameEngine:
    def __init__(self, width, height, arc_radius=350, zone_count=4, note_speed=3, hit_threshold=50, level=1, notes_per_beat=1, beatmap_file=None):
        self.width = width
        self.height = height
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.notes = []             
        self.spawn_timer = 0        
        self.level = level          
        self.notes_per_beat = notes_per_beat  

        self.beat_counter = 0
        self.last_spawned_beat = -1

        # === 譜面讀取 ===
        if beatmap_file:
            beatmap_path = os.path.join("beatmap", beatmap_file)
            self.rhythm_pattern = self.load_beatmap_from_file(beatmap_path)
        elif self.level == 1:
            beatmap_path = os.path.join("beatmap", "beatmap_level1.txt")
            if os.path.exists(os.path.join(os.path.dirname(__file__), beatmap_path)):
                self.rhythm_pattern = self.load_beatmap_from_file(beatmap_path)
            else:
                self.rhythm_pattern = []
        else:
            self.rhythm_pattern = [1, 0, 1, 0, 1, 1, 0, 1]
            
        if not self.rhythm_pattern:
            self.rhythm_pattern = [1, 0, 1, 0]

        self.pattern_length = len(self.rhythm_pattern)

        # === 幾何與判定參數 (還原回原本的設定) ===
        self.total_notes = 0        
        self.hit_notes = 0          
        self.miss_notes = 0         
        self.ARC_CENTER = (width // 2, height) 
        
        # 使用傳入的半徑 (通常是 width * 0.4)
        self.ARC_RADIUS = arc_radius          
        
        self.ZONE_COUNT = zone_count          
        self.ZONE_ANGLE_WIDTH = 180 / zone_count 
        
        # 還原：使用外部傳入的速度 (例如 7 或 8)
        self.NOTE_SPEED = note_speed          
        
        # 還原：原本較寬鬆的判定值
        self.HIT_THRESHOLD = 70               
        self.LINE_HIT_TOLERANCE = 80          
        self.NOTE_RADIUS = 30                 
        
        self.last_hit_note_id = -1
        self.next_note_id = 0 
        self.last_spawn_zones = []  

    def load_beatmap_from_file(self, relative_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, relative_path)
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                pattern = ast.literal_eval(content)
                return pattern
        except Exception:
            return []

    def _get_available_zones(self, count):
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
        if zone is None: zone = random.randint(0, self.ZONE_COUNT - 1)
        start_angle = 180 - (zone * self.ZONE_ANGLE_WIDTH)
        end_angle = 180 - ((zone + 1) * self.ZONE_ANGLE_WIDTH)
        angle = random.uniform(end_angle + 10, start_angle - 10)
        initial_radius = 50 
        note_type = 'normal'
        if self.level >= 1: 
            rand = random.random()
            if rand < 0.90: note_type = 'normal'
            else: note_type = 'bonus'
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
            if note['current_radius'] > self.ARC_RADIUS + self.LINE_HIT_TOLERANCE:
                note['active'] = False
                if note['status'] != 'hit':
                    note['status'] = 'miss'
                    self.miss_notes += 1
                    self.combo = 0 
                notes_to_remove.append(note)
        for note in notes_to_remove:
            if note in self.notes:
                self.notes.remove(note)

    def get_note_position(self, note):
        rad_angle = math.radians(note['angle'])
        x = int(self.ARC_CENTER[0] + note['current_radius'] * math.cos(rad_angle))
        y = int(self.ARC_CENTER[1] - note['current_radius'] * math.sin(rad_angle))
        return (x, y)

    def update_game_state(self, hand_pos, spawn_rate=60, music_controller=None):
        if music_controller is not None:
            current_beat = music_controller.get_current_beat_float()
            dist = self.ARC_RADIUS - 50
            frames = dist / self.NOTE_SPEED
            
            # 【重要】如果您覺得 1080p 球還是稍微有點對不上，可以微調這個 30.0
            sec_to_hit = frames / 30.0 
            
            if music_controller.bpm > 0:
                sec_per_beat = 60.0 / music_controller.bpm
            else:
                sec_per_beat = 1.0
            beats_travel_time = sec_to_hit / sec_per_beat
            target_beat = int(current_beat + beats_travel_time)
            if target_beat > self.last_spawned_beat:
                pattern_index = target_beat % self.pattern_length
                should_spawn = self.rhythm_pattern[pattern_index] == 1
                if should_spawn:
                    zones = self._get_available_zones(self.notes_per_beat)
                    for zone in zones: self._spawn_note(zone)
                    self.last_spawn_zones = zones
                self.last_spawned_beat = target_beat
        else:
            self.spawn_timer += 1
            if self.spawn_timer >= spawn_rate * 2:
                zones = self._get_available_zones(self.notes_per_beat)
                for zone in zones: self._spawn_note(zone)
                self.last_spawn_zones = zones
                self.spawn_timer = 0

        self._update_notes()
        
        if hand_pos is None:
            self.last_hit_note_id = -1
            return
            
        for note in self.notes:
            if not note['active'] or note['status'] == 'hit': continue
            note_x, note_y = self.get_note_position(note)
            dist_note_center = math.hypot(note_x - self.ARC_CENTER[0], note_y - self.ARC_CENTER[1])
            note_in_hit_zone = abs(dist_note_center - self.ARC_RADIUS) < self.LINE_HIT_TOLERANCE
            dist_hand_note = math.hypot(hand_pos[0] - note_x, hand_pos[1] - note_y)
            hand_touched_note = dist_hand_note < (self.NOTE_RADIUS + self.HIT_THRESHOLD)
            dist_hand_center = math.hypot(hand_pos[0] - self.ARC_CENTER[0], hand_pos[1] - self.ARC_CENTER[1])
            hand_on_line = abs(dist_hand_center - self.ARC_RADIUS) < self.LINE_HIT_TOLERANCE

            if note_in_hit_zone and hand_touched_note and hand_on_line:
                if note['id'] != self.last_hit_note_id:
                    note_type = note.get('type', 'normal')
                    if note_type == 'normal': self.score += 1
                    elif note_type == 'bonus': self.score += 2
                    note['status'] = 'hit'
                    self.hit_notes += 1
                    self.combo += 1
                    if self.combo > self.max_combo: self.max_combo = self.combo
                    self.last_hit_note_id = note['id']

    def get_notes_for_drawing(self):
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
    def get_combo(self): return self.combo