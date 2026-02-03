#!/usr/bin/env python
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IFPIChat.settings')
django.setup()

from collector.supabase_client import SupabaseClient

def debug_data():
    print("=== Debug dos Dados ===")
    
    # Verificar Supabase
    try:
        supabase = SupabaseClient()
        
        # Contar documentos (total real)
        import requests
        response = requests.head(
            f"{supabase.url}/rest/v1/documents",
            headers={**supabase.headers, "Prefer": "count=exact"}
        )
        doc_count = response.headers.get('Content-Range', '0').split('/')[-1]
        print(f"Documentos no banco: {doc_count}")
        
        # Contar chunks (total real)
        response = requests.head(
            f"{supabase.url}/rest/v1/document_chunks",
            headers={**supabase.headers, "Prefer": "count=exact"}
        )
        chunk_count = response.headers.get('Content-Range', '0').split('/')[-1]
        print(f"Chunks no banco: {chunk_count}")
            
        # Contar chunks com embeddings (total real)
        response = requests.head(
            f"{supabase.url}/rest/v1/document_chunks?embedding=not.is.null",
            headers={**supabase.headers, "Prefer": "count=exact"}
        )
        embed_count = response.headers.get('Content-Range', '0').split('/')[-1]
        print(f"Chunks com embeddings: {embed_count}")
            
        # Verificar se chunks têm embeddings (amostra)
        response = requests.get(
            f"{supabase.url}/rest/v1/document_chunks?select=id,chunk_text,embedding&limit=3",
            headers=supabase.headers
        )
        if response.status_code == 200:
            chunks = response.json()
            print(f"Exemplo de chunks: {len(chunks)} encontrados")
            for i, chunk in enumerate(chunks):
                has_embedding = chunk.get('embedding') is not None
                print(f"  Chunk {i+1}: {chunk['chunk_text'][:100]}... (embedding: {has_embedding})")
            
    except Exception as e:
        print(f"Erro Supabase: {e}")
        
    # Testar busca vetorial
    try:
        from collector.agent import answer_question
        print("\n=== Teste de Busca Vetorial ===")
        result = answer_question("Quais são os cursos do IFPI?", k=3)
        print(f"Resposta: {result['answer'][:100]}...")
        print(f"Citações encontradas: {len(result['citations'])}")
    except Exception as e:
        print(f"Erro no teste de busca: {e}")

if __name__ == "__main__":
    debug_data()