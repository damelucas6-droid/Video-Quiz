"""
Script de test bout-en-bout pour vérifier la génération complète d'une vidéo de quiz.
"""

import asyncio
import json
from pathlib import Path
import time
from moviepy import VideoFileClip

from main import (
    QuizPayload,
    execute_quiz_background_task,
    TASK_REGISTRY,
    TEMP_DIR,
    OUTPUT_DIR,
)

async def test_full_pipeline():
    task_id = "test_run"
    payload_data = json.loads(Path("sample_payload.json").read_text(encoding="utf-8"))
    payload = QuizPayload(**payload_data)

    TASK_REGISTRY[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "progress": 0,
    }

    print(f"Lancement du test bout-en-bout pour task_id '{task_id}'...")
    start_time = time.time()
    await execute_quiz_background_task(task_id, payload)
    elapsed = time.time() - start_time

    task_status = TASK_REGISTRY[task_id]
    print(f"Statut final de la tâche : {task_status['status']}")
    print(f"Message : {task_status.get('message')}")
    print(f"Temps écoulé : {elapsed:.2f} secondes")

    output_video = OUTPUT_DIR / f"quiz_{task_id}.mp4"
    assert output_video.exists(), f"La vidéo {output_video} n'a pas été créée."

    # Vérification des propriétés de la vidéo générée
    clip = VideoFileClip(str(output_video))
    print(f"Propriétés de la vidéo générée :")
    print(f"- Durée : {clip.duration:.2f} s (attendu: ~60.0 s)")
    print(f"- Résolution : {clip.size} (attendu: (1080, 1920))")
    print(f"- Audio présent : {clip.audio is not None}")
    print(f"- Taille fichier : {output_video.stat().st_size / (1024 * 1024):.2f} MB")

    assert tuple(clip.size) == (1080, 1920), f"Résolution incorrecte : {clip.size}"
    assert 59.0 <= clip.duration <= 61.0, f"Durée anormale : {clip.duration}"
    assert clip.audio is not None, "La piste audio globale est manquante !"

    clip.close()

    # Vérification du nettoyage du dossier temp/
    temp_leftover = list(TEMP_DIR.glob(f"{task_id}_*.mp3"))
    print(f"Fichiers restants dans temp/ pour cette tâche : {len(temp_leftover)}")
    assert len(temp_leftover) == 0, f"Le dossier temp contient des résidus : {temp_leftover}"

    print("\n[SUCCÈS TOTAL] La vidéo de 60s en 1080x1920 a été générée et validée avec succès !")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
