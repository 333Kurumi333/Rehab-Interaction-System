import librosa
import numpy as np
import os

# === 設定輸入 ===
MUSIC_FOLDER = "music"
MUSIC_FILENAME = "Zankoku na Tenshi no Te-ze.wav"

# === 設定過濾門檻 (0.3 ~ 0.5) ===
THRESHOLD = 0.8

def generate_beatmap():
    # 路徑設定
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, MUSIC_FOLDER, MUSIC_FILENAME)

    # 設定輸出檔名
    filename_no_ext = os.path.splitext(MUSIC_FILENAME)[0]
    
    # 1. 給遊戲讀的 (純陣列)
    OUTPUT_GAME_FILE = f"{filename_no_ext}.txt"
    # 2. 給人類看的 (時間對照表)
    OUTPUT_READABLE_FILE = f"{filename_no_ext}_readable.txt"
    
    OUTPUT_DIR = "beatmap"

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
    
    # 用來儲存人類可讀的列表
    readable_lines = []
    readable_lines.append(f"{'拍數(Beat)':<10} | {'時間(Time)':<12} | {'強度(Strength)':<15} | {'狀態(Status)'}")
    readable_lines.append("-" * 60)

    count_1 = 0
    
    for i, t in enumerate(beat_times):
        beat_index = int(t / beat_interval)
        
        if beat_index < len(rhythm_pattern):
            status = " " # 預設沒球
            strength_val = 0.0
            
            if i < len(beat_strengths):
                strength_val = beat_strengths[i]
                
                # 判斷是否出球
                if strength_val > THRESHOLD:
                    rhythm_pattern[beat_index] = 1
                    status = "⬤ HIT (出球)" # 視覺化
                    count_1 += 1
                else:
                    rhythm_pattern[beat_index] = 0
                    status = "   ..."      # 休息
            
            # 加入可讀列表
            # 格式：第幾拍 | 幾秒 | 能量強度 | 出球狀態
            line = f"{beat_index:<10} | {t:.3f}s       | {strength_val:.3f}           | {status}"
            readable_lines.append(line)

    # === 4. 存檔 ===
    target_dir = os.path.join(current_dir, OUTPUT_DIR)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # A. 存遊戲檔
    game_path = os.path.join(target_dir, OUTPUT_GAME_FILE)
    with open(game_path, "w", encoding="utf-8") as f:
        f.write(str(rhythm_pattern))

    # B. 存人類可讀檔
    readable_path = os.path.join(target_dir, OUTPUT_READABLE_FILE)
    with open(readable_path, "w", encoding="utf-8") as f:
        f.write("\n".join(readable_lines))

    print("\n" + "="*50)
    print("【✅ 分析完成】")
    print(f"1. 遊戲用檔案: {OUTPUT_GAME_FILE}")
    print(f"2. 人類對照表: {OUTPUT_READABLE_FILE} (請打開這個檢查時間點！)")
    print("-" * 50)
    print(f"⚠️  請手動修改 main.py 的 BPM 為: {bpm:.2f}")
    print("="*50)

if __name__ == "__main__":
    generate_beatmap()