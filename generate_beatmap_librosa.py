"""
Beatmap Generator using Librosa
自動分析音樂並生成節奏遊戲譜面
"""
import librosa
import numpy as np
import os

# === 設定 ===
CONFIG = {
    "music_folder": "music",
    "music_filename": "Zankoku na Tenshi no Te-ze.wav",
    "output_dir": "beatmap",
    "threshold_multiplier": 1.1,  # 門檻倍率 (1.0 ~ 1.3)
}


def load_audio(file_path):
    """載入音訊檔案"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到音樂檔案: {file_path}")
    return librosa.load(file_path, sr=None)


def analyze_beats(y, sr):
    """分析節拍，回傳 BPM、拍點時間、拍點強度"""
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    bpm = tempo.item() if hasattr(tempo, 'item') else float(tempo)
    
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    beat_strengths = onset_env[beat_frames]
    
    if len(beat_strengths) > 0:
        beat_strengths = librosa.util.normalize(beat_strengths)
    
    duration = librosa.get_duration(y=y, sr=sr)
    return bpm, beat_times, beat_strengths, duration


def create_pattern(bpm, beat_times, beat_strengths, duration, threshold_multiplier):
    """根據拍點強度生成遊戲譜面 (0/1 陣列)"""
    avg_interval = 60.0 / bpm
    total_beats = int(duration / avg_interval) + 5
    pattern = [0] * total_beats
    
    threshold = np.mean(beat_strengths) * threshold_multiplier
    readable_lines = [
        f"{'Index':<12} | {'Time':<12} | {'Strength':<15} | {'Status'}",
        "-" * 60
    ]
    hit_count = 0
    
    for t, strength in zip(beat_times, beat_strengths):
        idx = int(round(t / avg_interval))
        status = "   ..."
        
        if 0 <= idx < len(pattern) and strength >= threshold:
            pattern[idx] = 1
            status = "⬤ HIT"
            hit_count += 1
        
        readable_lines.append(f"{idx:<12} | {t:.3f}s       | {strength:.3f}           | {status}")
    
    return pattern, readable_lines, hit_count


def save_beatmap(pattern, readable_lines, output_dir, filename_no_ext):
    """儲存譜面檔案"""
    os.makedirs(output_dir, exist_ok=True)
    
    game_path = os.path.join(output_dir, f"{filename_no_ext}.txt")
    with open(game_path, "w", encoding="utf-8") as f:
        f.write(str(pattern))
    
    time_path = os.path.join(output_dir, f"{filename_no_ext}_time.txt")
    with open(time_path, "w", encoding="utf-8") as f:
        f.write("\n".join(readable_lines))
    
    return game_path, time_path


def generate_beatmap():
    """主函數：生成譜面"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, CONFIG["music_folder"], CONFIG["music_filename"])
    output_dir = os.path.join(current_dir, CONFIG["output_dir"])
    filename_no_ext = os.path.splitext(CONFIG["music_filename"])[0]
    
    print(f"🎵 分析中: {CONFIG['music_filename']} ...")
    
    # 1. 載入音訊
    y, sr = load_audio(file_path)
    
    # 2. 分析節拍
    bpm, beat_times, beat_strengths, duration = analyze_beats(y, sr)
    print(f"BPM: {bpm:.2f}")
    
    if len(beat_strengths) == 0:
        print("警告：未偵測到節拍點")
        return
    
    # 3. 生成譜面
    pattern, readable_lines, hit_count = create_pattern(
        bpm, beat_times, beat_strengths, duration, CONFIG["threshold_multiplier"]
    )
    
    # 4. 儲存
    game_path, time_path = save_beatmap(pattern, readable_lines, output_dir, filename_no_ext)
    
    print(f"\n✅ 譜面生成完成！")
    print(f"   遊戲譜面: {os.path.basename(game_path)}")
    print(f"   時間對照: {os.path.basename(time_path)}")
    print(f"   總拍點: {len(beat_times)}, 音符數: {hit_count}")
    print(f"⚠️  請在 main.py 設定 BPM 為: {int(round(bpm))}")


if __name__ == "__main__":
    generate_beatmap()