import os
from openai import OpenAI

try:
    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
except KeyError:
    raise ValueError("Missing required environment variable: OPENROUTER_API_KEY")


system = """
Você é um gerador de títulos para conversas sobre o ENEM.
Crie um título curto, claro e informativo (máx. 8 palavras).
O título deve refletir o conteúdo educacional da pergunta.
Use termos do ENEM quando possível (redação, competências, prova, nota, áreas).
Não use pontuação final.
Não use frases genéricas.
Não explique o título.
Retorne apenas o título.
"""

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def title_generator(question: str) -> str:
    free_models = [
        "openai/gpt-oss-120b:free",
        "openai/gpt-oss-20b:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "google/gemma-3-27b-it:free"
    ]
    
    answer_text = None
    for model in free_models:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": question}
                ],
                max_tokens=2048,
                timeout=30
            )
            answer_text = completion.choices[0].message.content
            break  # Sucesso, sair do loop
        except Exception as e:
            print(f"Erro com modelo {model}: {e}")
            continue
    
    if not answer_text:
        return ""
    
    return answer_text