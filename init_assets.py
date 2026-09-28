"""
Script d'initialisation et de génération des assets par défaut pour le projet Quiz Vidéo.
Crée les fichiers suivants s'ils n'existent pas déjà :
- assets/fonts/Montserrat-Black.ttf
- assets/sfx/tick.mp3 (compte à rebours 5s)
- assets/sfx/correct.mp3 (chime de validation)
- assets/sfx/music.mp3 (musique de fond d'ambiance)
- assets/backgrounds/default.mp4 (fond vidéo vertical 1080x1920)
"""

import math
from pathlib import Path
import shutil
import struct
import subprocess
import urllib.request
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
SFX_DIR = ASSETS_DIR / "sfx"
BG_DIR = ASSETS_DIR / "backgrounds"

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def init_font():
    font_path = FONTS_DIR / "Montserrat-Black.ttf"
    if font_path.exists():
        print(f"[OK] Police déjà présente : {font_path}")
        return

    print("Téléchargement de la police Montserrat-Black.ttf...")
    url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf"
    try:
        urllib.request.urlretrieve(url, str(font_path))
        print(f"[OK] Montserrat-Black téléchargée dans {font_path}")
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible de télécharger la police ({e}). Copie du fallback système...")
        arial_path = Path("C:/Windows/Fonts/arialbd.ttf")
        if arial_path.exists():
            shutil.copy(arial_path, font_path)
            print(f"[OK] Fallback arialbd.ttf copié vers {font_path}")
        else:
            print("[ERREUR] Aucune police système trouvée.")


def generate_wav_and_convert_to_mp3(samples: list[float], sample_rate: int, output_mp3: Path):
    temp_wav = output_mp3.with_suffix(".wav")
    import wave
    with wave.open(str(temp_wav), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        int_samples = [int(max(-1.0, min(1.0, s)) * 32767) for s in samples]
        data = struct.pack("<" + ("h" * len(int_samples)), *int_samples)
        wf.writeframes(data)

    cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(temp_wav),
        "-codec:a", "libmp3lame",
        "-b:a", "192k",
        str(output_mp3)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if temp_wav.exists():
        temp_wav.unlink()
    print(f"[OK] Audio généré : {output_mp3}")


def init_sfx():
    sample_rate = 44100

    # 1. tick.mp3 (5 secondes de compte à rebours : 5 bips percutants)
    tick_path = SFX_DIR / "tick.mp3"
    if not tick_path.exists():
        duration = 5.0
        n_samples = int(sample_rate * duration)
        samples = [0.0] * n_samples
        for sec in range(5):
            start = int(sec * sample_rate)
            tick_len = int(sample_rate * 0.08)  # 80ms
            freq = 1200 if sec < 4 else 1800  # tonalité plus aiguë au 5ème bip
            for i in range(tick_len):
                t = i / sample_rate
                decay = math.exp(-t * 50)
                samples[start + i] = 0.7 * math.sin(2 * math.pi * freq * t) * decay
        generate_wav_and_convert_to_mp3(samples, sample_rate, tick_path)
    else:
        print(f"[OK] SFX tick déjà présent : {tick_path}")

    # 2. correct.mp3 (Chime harmonieux ascendant C5 -> G5)
    correct_path = SFX_DIR / "correct.mp3"
    if not correct_path.exists():
        duration = 1.2
        n_samples = int(sample_rate * duration)
        samples = [0.0] * n_samples
        t_note2 = int(0.15 * sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            decay1 = math.exp(-t * 5)
            s1 = 0.4 * math.sin(2 * math.pi * 523.25 * t) * decay1
            s2 = 0.0
            if i >= t_note2:
                t2 = (i - t_note2) / sample_rate
                decay2 = math.exp(-t2 * 4)
                s2 = 0.5 * (
                    math.sin(2 * math.pi * 783.99 * t2)
                    + 0.25 * math.sin(2 * math.pi * 1567.98 * t2)
                ) * decay2
            samples[i] = s1 + s2
        generate_wav_and_convert_to_mp3(samples, sample_rate, correct_path)
    else:
        print(f"[OK] SFX correct déjà présent : {correct_path}")

    # 3. music.mp3 (Musique de fond d'ambiance Lo-Fi / Synthwave 12s bouclable)
    music_path = SFX_DIR / "music.mp3"
    if not music_path.exists():
        duration = 12.0
        n_samples = int(sample_rate * duration)
        samples = [0.0] * n_samples
        chords = [
            [220.00, 261.63, 329.63],  # Am
            [174.61, 220.00, 261.63],  # F
            [130.81, 164.81, 196.00],  # C
            [196.00, 246.94, 293.66],  # G
        ]
        for chord_idx, chord_notes in enumerate(chords):
            start_sample = int(chord_idx * 3.0 * sample_rate)
            end_sample = int((chord_idx + 1) * 3.0 * sample_rate)
            for i in range(start_sample, min(end_sample, n_samples)):
                t = (i - start_sample) / sample_rate
                envelope = min(1.0, t * 4.0) * min(1.0, (3.0 - t) * 4.0)
                chord_val = 0.0
                for freq in chord_notes:
                    chord_val += 0.15 * math.sin(2 * math.pi * freq * t)
                    chord_val += 0.05 * math.sin(2 * math.pi * freq * 2 * t)
                bass = 0.12 * math.sin(2 * math.pi * (chord_notes[0] / 2) * t)
                samples[i] = (chord_val + bass) * envelope
        generate_wav_and_convert_to_mp3(samples, sample_rate, music_path)
    else:
        print(f"[OK] Musique de fond déjà présente : {music_path}")


def init_background_video():
    bg_video_path = BG_DIR / "default.mp4"
    if bg_video_path.exists():
        print(f"[OK] Vidéo de fond déjà présente : {bg_video_path}")
        return

    print("Génération de la vidéo de fond verticale (1080x1920, 12s)...")
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "lavfi",
        "-i", "color=c=0x111322:s=1080x1920:d=12:r=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        str(bg_video_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[OK] Vidéo de fond générée : {bg_video_path}")


if __name__ == "__main__":
    print("Initialisation des répertoires et assets du projet...")
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    BG_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "output").mkdir(exist_ok=True)
    (BASE_DIR / "temp").mkdir(exist_ok=True)

    init_font()
    init_sfx()
    init_background_video()
    print("Tous les assets par défaut sont prêts !")
