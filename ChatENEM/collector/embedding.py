import os
import requests
import time
from typing import List

HF_MODEL = "intfloat/multilingual-e5-large"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}/pipeline/feature-extraction"


def embed_batch(
    texts: List[str],
    mode: str = "document"  # "document" ou "query"
) -> List[List[float]]:
    """
    Gera embeddings semânticos para o ChatENEM usando Hugging Face (gratuito).

    Args:
        texts: Lista de textos (editais, provas, perguntas, etc.)
        mode: 
            - "document" → para materiais do ENEM
            - "query" → para perguntas do usuário

    Returns:
        Lista de vetores (embeddings)
    """

    api_token = os.environ.get("HF_TOKEN")
    if not api_token:
        raise RuntimeError(
            "HF_TOKEN não configurado. Defina a variável de ambiente no Render."
        )

    # Prefixo semântico recomendado pelo modelo E5
    if mode == "query":
        prefixed_texts = [f"query: {t}" for t in texts]
    else:
        prefixed_texts = [f"passage: {t}" for t in texts]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    payload = {
        "inputs": prefixed_texts,
        "options": {
            "wait_for_model": True
        }
    }

    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        # Modelo carregando
        if response.status_code == 503:
            time.sleep(20)
            response = requests.post(
                HF_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"HF API error {response.status_code}: {response.text}"
            )

        return response.json()

    except Exception as e:
        raise RuntimeError(f"Erro ao gerar embeddings do ENEM: {e}") from e
