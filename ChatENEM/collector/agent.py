import os
import requests
from typing import List, Dict, Tuple
from openai import OpenAI

from .embedding import embed_batch
from .supabase_client import SupabaseClient

try:
    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
except KeyError:
    raise ValueError("Missing required environment variable: OPENROUTER_API_KEY")

# Cliente OpenAI configurado para OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

NO_CONTEXT_ANSWER = (
    "Não tenho essa informação disponível com base nos documentos do ENEM."
)


SYSTEM_PROMPT = (
    "Você é o assistente educacional oficial do ENEM (Exame Nacional do Ensino Médio), "
    "responsável por orientar estudantes com base exclusivamente em documentos oficiais do INEP/MEC.\n\n"
    "Regras:\n"
    "• Responder APENAS com informações presentes no contexto fornecido\n"
    "• Não inventar, interpretar ou extrapolar informações\n"
    "• Usar linguagem clara, objetiva e educacional\n"
    "• Explicar conceitos quando o contexto permitir\n"
    f"• Se a resposta não estiver no contexto, responder exatamente: '{NO_CONTEXT_ANSWER}'"
)



def _get_similar_chunks(question: str, k: int = 5) -> Tuple[List[Dict], List[float]]:
    """
    Retorna os k DocumentChunk mais similares usando pgvector.
    """
    try:
        print(f"DEBUG: Buscando chunks para: {question}")
        # Gerar embedding da pergunta
        question_embedding = embed_batch([question])[0]
        print(f"DEBUG: Embedding gerado: {len(question_embedding)} dimensões")
        
        supabase = SupabaseClient()
        
        # Busca usando pgvector
        response = requests.post(
            f"{supabase.url}/rest/v1/rpc/search_chunks",
            headers=supabase.headers,
            json={"query_embedding": question_embedding, "match_count": k}
        )
        
        print(f"DEBUG: Status da busca: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"DEBUG: Resultados encontrados: {len(results)}")
            print(f"DEBUG: chunk: {results}")
            chunks = []
            scores = []
            
            for result in results:
                chunks.append(result)
                scores.append(result.get('similarity', 0.0))
            
            print(f"DEBUG: Retornando {len(chunks)} chunks")
            return chunks, scores
        else:
            print(f"DEBUG: Erro na resposta: {response.text}")
            return [], []
            
    except Exception as e:
        print(f"Erro na busca vetorial: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def _build_prompt(question: str, chunks: List[Dict]) -> str:
    """
    Constrói o prompt do usuário incorporando os chunks como contexto.
    """
    parts = []
    for c in chunks:
        doc = c.get("documents")
        src = (doc.get("title") or doc.get("source")) if doc else f"document_id={c.get('document_id')}"
        parts.append(f"Fonte: {src}\nTrecho:\n{c.get('chunk_text', '').strip()}")
    contexto = "\n\n---\n\n".join(parts) if parts else ""
    user_prompt = (
        f"Pergunta: {question}\n\n"
        f"Contexto (use apenas o que está aqui para responder):\n{contexto}\n\n"
        f"Responda de forma direta e curta. "
        f"Se não houver informação suficiente no contexto, responda exatamente: '{NO_CONTEXT_ANSWER}'"

    )
    return user_prompt

def answer_question(question: str, k: int = 5) -> Dict:
    """
    Fluxo principal:
      - obter top-k chunks similares via pgvector,
      - montar prompt,
      - chamar LLM (OpenAI/OpenRouter) e retornar resposta + citações.
    """
    chunks, scores = _get_similar_chunks(question, k)
    
    if not chunks:
        return {
            "answer": NO_CONTEXT_ANSWER,
            "citations": [],
            "found_context": False,
        }
    
    system = SYSTEM_PROMPT
    user = _build_prompt(question, chunks)

    # Modelos gratuitos para fallback
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
                    {"role": "user", "content": user}
                ],
                max_tokens=2048,
                
            )
            answer_text = completion.choices[0].message.content
            break  # Sucesso, sair do loop
        except Exception as e:
            print(f"Erro com modelo {model}: {e}")
            continue
    
    if not answer_text:
        return {
            "answer": "Serviço temporariamente indisponível. Tente novamente mais tarde.",
            "citations": [],
            "found_context": False,
        }
    
    # Sempre incluir citações quando há chunks encontrados
    citations = []
    if chunks:
        for c, s in zip(chunks, scores):
            try:
                doc = c.get("documents")
                chunk_text = c.get("chunk_text", "")
                citations.append({
                    "chunk_id": c.get("id"),
                    "score": float(s),
                    "document_title": doc.get("title") if doc else None,
                    "document_source": doc.get("source") if doc else None,
                    "excerpt": (chunk_text[:400] + "...") if len(chunk_text) > 400 else chunk_text,
                })
            except Exception:
                continue

    return {
        "answer": answer_text or NO_CONTEXT_ANSWER,
        "citations": citations,
        "found_context": bool(chunks),
    }