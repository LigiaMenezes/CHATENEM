from typing import List, Dict, Any, Optional
import os
import requests
import hashlib
from .embedding import embed_batch

class DatabaseLayer:
    """
    Camada de persistência com Supabase
    Inserção idempotente e geração de embeddings
    """

    def __init__(self, supabase_url: str, supabase_key: str, embedding_model: str = "all-MiniLM-L6-v2"):
        self.url = supabase_url
        self.headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        self.embedding_model = embedding_model

    def insert_document(self, url: str, title: str, source_type: str = "web") -> Optional[str]:
        """
        Insere documento no banco

        Returns:
            ID do documento inserido ou None se erro
        """
        try:
            # Normalizar URL para deduplicação
            from urllib.parse import urlparse, urljoin
            parsed = urlparse(url)
            url_norm = f"{parsed.scheme}://{parsed.netloc.replace('www.', '')}{parsed.path.rstrip('/')}"
            if parsed.query:
                url_norm += f"?{parsed.query}"

            doc_data = {
                'url': url,
                'url_norm': url_norm,  # URL normalizada para deduplicação
                'title': title,
                'source': source_type,
                'created_at': 'now()'
            }

            response = requests.post(
                f"{self.url}/rest/v1/documents",
                headers=self.headers,
                json=doc_data
            )

            if response.status_code in [200, 201]:
                # Buscar ID do documento inserido
                search_response = requests.get(
                    f"{self.url}/rest/v1/documents?url_norm=eq.{url_norm}&select=id",
                    headers=self.headers
                )

                if search_response.status_code == 200:
                    docs = search_response.json()
                    if docs:
                        return docs[0]['id']

            print(f"Erro inserindo documento: {response.status_code} - {response.text}")
            return None

        except Exception as e:
            print(f"Erro inserindo documento: {e}")
            return None

    def insert_chunks(self, chunks: List[Dict[str, Any]], document_id: Optional[str] = None) -> Dict[str, int]:
        """
        Insere chunks com idempotência via hash

        Args:
            chunks: Lista de chunks semânticos
            document_id: ID do documento pai (opcional)

        Returns:
            {
                'inserted': int,
                'skipped': int,
                'errors': int
            }
        """
        inserted = 0
        skipped = 0
        errors = 0

        for chunk in chunks:
            try:
                chunk_hash = chunk.get('hash')

                # Verificar se chunk já existe
                exists_response = requests.get(
                    f"{self.url}/rest/v1/document_chunks?chunk_hash=eq.{chunk_hash}&select=id",
                    headers=self.headers
                )

                if exists_response.status_code == 200 and exists_response.json():
                    skipped += 1
                    continue

                # Gerar embedding
                text = chunk.get('text', '')
                if text:
                    try:
                        embedding = embed_batch([text])[0]
                    except Exception as e:
                        print(f"Erro gerando embedding para chunk {chunk_hash}: {e}")
                        embedding = None
                else:
                    embedding = None

                # Preparar dados para inserção
                chunk_data = {
                    'document_id': document_id,  # FK para documents
                    'chunk_hash': chunk_hash,  # Hash do conteúdo para verificação
                    'chunk_text': text,
                    'embedding': embedding,
                    'embedding_model': self.embedding_model,  # Modelo usado para embedding
                    'metadata': {
                        **chunk.get('metadata', {}),
                        "domain": "ENEM",
                        "institution": "INEP/MEC",
                        "language": "pt-BR",
                    },
                    'created_at': 'now()'
                }

                # Inserir
                response = requests.post(
                    f"{self.url}/rest/v1/document_chunks",
                    headers=self.headers,
                    json=chunk_data
                )

                if response.status_code in [200, 201]:
                    inserted += 1
                else:
                    print(f"Erro inserindo chunk {chunk_hash}: {response.status_code} - {response.text}")
                    errors += 1

            except Exception as e:
                print(f"Erro processando chunk: {e}")
                errors += 1

        return {
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors
        }

    def search_similar_chunks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca chunks similares usando embeddings

        Args:
            query: Texto da consulta
            limit: Número máximo de resultados

        Returns:
            Lista de chunks similares
        """
        try:
            # Gerar embedding da query
            query_embedding = embed_batch([query])[0]

            # Buscar via RPC do Supabase
            response = requests.post(
                f"{self.url}/rest/v1/rpc/search_chunks",
                headers=self.headers,
                json={
                    "query_embedding": query_embedding,
                    "match_count": limit
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro na busca: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"Erro na busca vetorial: {e}")
            return []

    def get_stats(self) -> Dict[str, int]:
        """
        Retorna estatísticas do banco

        Returns:
            {
                'documents': int,
                'chunks': int,
                'chunks_with_embeddings': int
            }
        """
        try:
            stats = {}

            # Contar documentos
            response = requests.head(
                f"{self.url}/rest/v1/documents",
                headers={**self.headers, "Prefer": "count=exact"}
            )
            stats['documents'] = int(response.headers.get('Content-Range', '0').split('/')[-1])

            # Contar chunks
            response = requests.head(
                f"{self.url}/rest/v1/document_chunks",
                headers={**self.headers, "Prefer": "count=exact"}
            )
            stats['chunks'] = int(response.headers.get('Content-Range', '0').split('/')[-1])

            # Contar chunks com embeddings
            response = requests.head(
                f"{self.url}/rest/v1/document_chunks?embedding=not.is.null",
                headers={**self.headers, "Prefer": "count=exact"}
            )
            stats['chunks_with_embeddings'] = int(response.headers.get('Content-Range', '0').split('/')[-1])

            return stats

        except Exception as e:
            print(f"Erro obtendo estatísticas: {e}")
            return {'documents': 0, 'chunks': 0, 'chunks_with_embeddings': 0}
