import requests
import json
from django.conf import settings
from typing import List, Dict, Optional

class SupabaseClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def create_document(self, title: str = None, source: str = "", url: str = "") -> Dict:
        """Cria um documento via API Supabase"""
        def _normalize(u: str) -> str:
            if not u:
                return ''
            from urllib.parse import urlparse
            u = u.strip().lower()
            parsed = urlparse(u)
            netloc = (parsed.netloc or '').replace('www.', '')
            path = (parsed.path or '').rstrip('/')
            query = parsed.query or ''
            key = netloc + path
            if query:
                key = f"{key}?{query}"
            return key

        def _variants(u: str) -> List[str]:
            # gera variantes simples: http/https e com/sem www, com/sem trailing slash
            if not u:
                return []
            from urllib.parse import urlparse
            parsed = urlparse(u)
            host = (parsed.netloc or '')
            path = parsed.path or ''
            qs = ('?' + parsed.query) if parsed.query else ''
            host_no_www = host.replace('www.', '')
            vs = []
            for scheme in ['http', 'https']:
                for h in [host_no_www, ('www.' + host_no_www)]:
                    vs.append(f"{scheme}://{h}{path}{qs}")
                    if path and not path.endswith('/'):
                        vs.append(f"{scheme}://{h}{path.rstrip('/')}/{qs}")
            # dedupe preserving order
            seen = []
            for v in vs:
                if v not in seen:
                    seen.append(v)
            return seen

        data = {"title": title, "source": source, "url": url}

        try:
            norm = _normalize(url)

            # 1) tentar encontrar por url_norm (mais robusto)
            if norm:
                resp = requests.get(
                    f"{self.url}/rest/v1/documents?url_norm=eq.{norm}",
                    headers=self.headers
                )
                if resp.status_code == 200 and resp.text.strip():
                    try:
                        items = resp.json()
                        if items:
                            return items[0]
                    except Exception:
                        pass

            # 2) fallback: buscar por variantes diretas no campo url
            variants = _variants(url)
            if variants:
                in_list = ','.join([f'"{v}"' for v in variants])
                resp2 = requests.get(
                    f"{self.url}/rest/v1/documents?url=in.({in_list})",
                    headers=self.headers
                )
                if resp2.status_code == 200 and resp2.text.strip():
                    try:
                        items = resp2.json()
                        if items:
                            return items[0]
                    except Exception:
                        pass

            # 3) não existe → criar incluindo url_norm
            data['url_norm'] = norm
            response = requests.post(
                f"{self.url}/rest/v1/documents",
                headers=self.headers,
                json=data
            )
            print(f"Document creation - Status: {response.status_code}, Response: {response.text}")
            if response.status_code in (200, 201):
                if response.text.strip():
                    return response.json()[0]
                return None
            return None
        except Exception as e:
            print(f"Error creating document: {e}")
            return None
    
    def create_chunk(self, document_id: int, chunk_text: str, chunk_hash: str, embedding_model: str = "intfloat/multilingual-e5-large") -> Dict:
        """Cria um chunk via API Supabase"""
        data = {
            "document_id": document_id,
            "chunk_text": chunk_text,
            "chunk_hash": chunk_hash,
            "embedding_model": embedding_model
        }
        try:
            response = requests.post(
                f"{self.url}/rest/v1/document_chunks",
                headers=self.headers,
                json=data
            )
            print(f"Chunk creation - Status: {response.status_code}, Response: {response.text}")
            if response.status_code == 201:
                if response.text.strip():
                    return response.json()[0]
                else:
                    # Supabase retornou vazio, criar um mock ID
                    import time
                    return {"id": int(time.time() * 1000)}  # ID baseado em timestamp
            return None
        except Exception as e:
            print(f"Error creating chunk: {e}")
            return None
    
    def get_chunks_by_ids(self, chunk_ids: List[int]) -> List[Dict]:
        """Busca chunks por IDs via API Supabase"""
        ids_str = ",".join(map(str, chunk_ids))
        response = requests.get(
            f"{self.url}/rest/v1/document_chunks?id=in.({ids_str})&select=*,documents(*)",
            headers=self.headers
        )
        return response.json() if response.status_code == 200 else []
    
    def check_existing_hashes(self, hashes: List[str]) -> List[str]:
        """Verifica quais hashes já existem"""
        hashes_str = ",".join([f'"{h}"' for h in hashes])
        response = requests.get(
            f"{self.url}/rest/v1/document_chunks?chunk_hash=in.({hashes_str})&select=chunk_hash",
            headers=self.headers
        )
        if response.status_code == 200:
            return [item["chunk_hash"] for item in response.json()]
        return []
    
    def search_chunks(self, query_embedding: List[float], match_count: int = 5) -> List[Dict]:
        """Busca chunks similares usando pgvector"""
        response = requests.post(
            f"{self.url}/rest/v1/rpc/search_chunks",
            headers=self.headers,
            json={"query_embedding": query_embedding, "match_count": match_count}
        )
        return response.json() if response.status_code == 200 else []

    def delete_documents_with_url_substrings(self, substrings: List[str]) -> Dict:
        """Deleta documentos (e seus chunks) cujas URLs contenham qualquer uma das substrings.

        Retorna um dicionário com a lista de documentos deletados ou erro.
        """
        deleted = []
        try:
            for sub in substrings:
                # Construir filtro like para Supabase REST: url=like.%25<sub>%25
                filter_url = f"{self.url}/rest/v1/documents?select=id,url&url=like.%25{sub}%25"
                resp = requests.get(filter_url, headers=self.headers)
                if resp.status_code != 200:
                    print(f"Falha ao buscar documentos para '{sub}': {resp.status_code}")
                    continue
                items = resp.json() or []
                for doc in items:
                    doc_id = doc.get('id')
                    if not doc_id:
                        continue
                    # Deletar chunks associados
                    try:
                        requests.delete(f"{self.url}/rest/v1/document_chunks?document_id=eq.{doc_id}", headers=self.headers)
                    except Exception as e:
                        print(f"Erro ao deletar chunks do documento {doc_id}: {e}")
                    # Deletar documento
                    del_resp = requests.delete(f"{self.url}/rest/v1/documents?id=eq.{doc_id}", headers=self.headers)
                    if del_resp.status_code in (200, 204):
                        deleted.append(doc)
                        print(f"Documento deletado: {doc}")
                    else:
                        print(f"Falha ao deletar documento {doc_id}: {del_resp.status_code} - {del_resp.text}")

            return {"deleted": deleted}
        except Exception as e:
            print(f"Erro durante exclusão: {e}")
            return {"error": str(e)}