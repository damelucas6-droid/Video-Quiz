"""
Script de tests automatisés pour valider :
1. La validation stricte Pydantic (refus si != 5 questions, refus si reponse_correcte invalide)
2. La structure et la réponse immédiate de l'endpoint POST /generate-quiz
"""

import json
from pathlib import Path
from pydantic import ValidationError
from starlette.testclient import TestClient

from main import app, QuestionItem, QuizPayload, StyleConfig

client = TestClient(app)

def test_pydantic_validation_success():
    """Valide qu'un payload avec exactement 5 questions est accepté."""
    payload_data = json.loads(Path("sample_payload.json").read_text(encoding="utf-8"))
    payload = QuizPayload(**payload_data)
    assert len(payload.questions) == 5
    assert payload.questions[0].reponse_correcte == "B"
    assert payload.style.voice_name == "fr-FR-HenriNeural"


def test_pydantic_validation_rejects_non_5_questions():
    """Vérifie le rejet strict si le nombre de questions est différent de 5."""
    payload_data = json.loads(Path("sample_payload.json").read_text(encoding="utf-8"))
    # On supprime une question -> 4 questions au lieu de 5
    payload_data["questions"] = payload_data["questions"][:4]

    failed = False
    try:
        QuizPayload(**payload_data)
    except ValidationError as e:
        failed = True
        assert "5 questions" in str(e)
    assert failed, "La validation aurait dû échouer pour 4 questions."


def test_pydantic_validation_rejects_invalid_answer():
    """Vérifie le rejet si reponse_correcte n'est pas A, B, C ou D."""
    payload_data = json.loads(Path("sample_payload.json").read_text(encoding="utf-8"))
    payload_data["questions"][0]["reponse_correcte"] = "E"

    failed = False
    try:
        QuizPayload(**payload_data)
    except ValidationError as e:
        failed = True
        assert "La réponse correcte doit être 'A', 'B', 'C' ou 'D'" in str(e)
    assert failed, "La validation aurait dû échouer pour une réponse 'E'."


def test_api_root():
    """Vérifie l'endpoint GET /."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "1080x1920" in data["specs"]["format"]


def test_post_generate_quiz_validation_error():
    """Vérifie le code HTTP 422 si le payload envoyé à l'API est invalide."""
    payload_data = json.loads(Path("sample_payload.json").read_text(encoding="utf-8"))
    payload_data["questions"] = payload_data["questions"][:3]  # 3 questions

    response = client.post("/generate-quiz", json=payload_data)
    assert response.status_code == 422
    assert "5 questions" in response.text


if __name__ == "__main__":
    print("Exécution des tests de validation...")
    test_pydantic_validation_success()
    print("[PASS] Validation avec 5 questions réussie.")
    test_pydantic_validation_rejects_non_5_questions()
    print("[PASS] Rejet strict si != 5 questions validé.")
    test_pydantic_validation_rejects_invalid_answer()
    print("[PASS] Rejet d'une réponse incorrecte validé.")
    test_api_root()
    print("[PASS] Endpoint racine GET / validé.")
    test_post_generate_quiz_validation_error()
    print("[PASS] Rejet HTTP 422 sur POST /generate-quiz validé.")
    print("\nTous les tests unitaires ont réussi avec succès !")
