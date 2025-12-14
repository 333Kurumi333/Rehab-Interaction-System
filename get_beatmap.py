import librosa
import numpy as np
import os

# === 設定輸入 (音樂來源) ===
MUSIC_FOLDER = "music"
MUSIC_FILENAME = "Haruhikage_CRYCHIC.wav"

# === 自動設定輸出檔名 ===
# 1. 去除副檔名 (例如 .wav) 取得主檔名: "Haruhikage_CRYCHIC"
filename_no_ext = os.path.splitext(MUSIC_FILENAME)[0]
# 2. 加上 .txt
OUTPUT_FILENAME = f"{filename_no_ext}.txt"
# 3. 指定資料夾
OUTPUT_DIR = "beatmap"

# === 設定過濾門檻 ===
THRESHOLD = 0.5

def generate_beatmap():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, MUSIC_FOLDER, MUSIC_FILENAME)

    if not os.path.exists(file_path):
        print(f"錯誤：找不到音樂檔案！\n請確認檔案位於: {file_path}")
        return

    print(f"正在分析音樂: {MUSIC_FILENAME}")
    
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"讀取失敗: {e}")
        return

    # 1. 偵測 BPM
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if hasattr(tempo, 'item'):
        bpm = tempo.item()
    else:
        bpm = float(tempo)
        
    print(f"偵測到的 BPM: {bpm:.2f}")

    # 2. 計算能量強度
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    beat_strengths = librosa.util.sync(onset_env, beat_frames, aggregate=np.median)
    beat_strengths = librosa.util.normalize(beat_strengths)

    # 3. 產生譜面
    duration = librosa.get_duration(y=y, sr=sr)
    beat_interval = 60.0 / bpm
    total_beats = int(duration / beat_interval) + 1
    
    rhythm_pattern = [0] * total_beats
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    count_1 = 0
    count_0 = 0

    for i, t in enumerate(beat_times):
        beat_index = int(t / beat_interval)
        if beat_index < len(rhythm_pattern):
            if i < len(beat_strengths):
                strength = beat_strengths[i]
                if strength > THRESHOLD:
                    rhythm_pattern[beat_index] = 1
                    count_1 += 1
                else:
                    rhythm_pattern[beat_index] = 0
                    count_0 += 1

    # === 4. 自動存檔 ===
    target_dir = os.path.join(current_dir, OUTPUT_DIR)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    save_path = os.path.join(target_dir, OUTPUT_FILENAME)

    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(str(rhythm_pattern))
            
        print("\n" + "="*50)
        print("【✅ 成功！譜面已存入 beatmap 資料夾】")
        print(f"檔名: {OUTPUT_FILENAME}")
        print("-" * 50)
        print(f"總拍數: {len(rhythm_pattern)}")
        print(f"球數: {count_1} | 休息: {count_0}")
        print("-" * 50)
        print(f"⚠️  請記得更新 main.py 的 BPM 為: {bpm:.2f}")
        print("="*50)
        
    except Exception as e:
        print(f"存檔失敗: {e}")

if __name__ == "__main__":
    generate_beatmap()