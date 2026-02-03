import json
import os
from typing import Set, List
from urllib.parse import urlparse, urljoin
import hashlib

class URLManager:
    """
    Gerencia URLs visitadas e pendentes com checkpoint persistente
    (Scraping oficial do ENEM – INEP / MEC)
    """

    def __init__(self, checkpoint_file: str = "ChatENEM\data\enem_scraping_checkpoint.json", domain_filter: str = None):
        self.checkpoint_file = checkpoint_file
        self.domain_filter = domain_filter
        self.visited_urls: Set[str] = set()
        self.pending_urls: Set[str] = set()
        self.load_checkpoint()

    def normalize_url(self, url: str) -> str:
        """Normaliza URL: HTTPS, sem www, sem trailing slash"""
        if not url:
            return ""

        # Parse URL
        parsed = urlparse(url)

        # Forçar HTTPS
        scheme = 'https' if parsed.scheme == 'http' else parsed.scheme

        # Remover www
        netloc = parsed.netloc.replace('www.', '')

        # Remover trailing slash exceto para raiz
        path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path

        # Reconstruir
        normalized = f"{scheme}://{netloc}{path}"

        # Adicionar query se existir
        if parsed.query:
            normalized += f"?{parsed.query}"

        return normalized

    def is_valid_url(self, url: str) -> bool:
        """Verifica se URL é válida e dentro do domínio permitido"""
        if not url:
            return False

        try:
            
            parsed = urlparse(url)
            # Deve ter scheme e netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Filtrar domínio se especificado
            if self.domain_filter:
                if parsed.netloc.replace('www.', '') != self.domain_filter.replace('www.', ''):
                    return False

            # Ignorar âncoras
            if parsed.fragment:
                return False

            if "@" in url or "@@" in url:
                return False

            # Verificar extensão de arquivo se for um arquivo
            path = parsed.path.lower()
            if '.' in path:
                # É um arquivo, verificar extensão
                _, ext = os.path.splitext(path)
                allowed_exts = {'.doc', '.docx', '.pdf', '.rar', '.zip'}
                if ext not in allowed_exts:
                    return False

            return True
        except:
            return False

    def add_pending_url(self, url: str):
        """Adiciona URL à fila pendente se válida e não visitada"""
        normalized = self.normalize_url(url)
        if self.is_valid_url(normalized) and normalized not in self.visited_urls:
            self.pending_urls.add(normalized)

    def mark_visited(self, url: str):
        """Marca URL como visitada"""
        normalized = self.normalize_url(url)
        self.visited_urls.add(normalized)
        self.pending_urls.discard(normalized)
        self.save_checkpoint()

    def get_next_pending(self) -> str:
        """Retorna próxima URL pendente"""
        if self.pending_urls:
            return self.pending_urls.pop()
        return None

    def add_seed_urls(self, urls: List[str]):
        """Adiciona URLs iniciais"""
        for url in urls:
            self.add_pending_url(url)

    def save_checkpoint(self):
        """Salva estado atual em arquivo"""
        data = {
            "visited_urls": list(self.visited_urls),
            "pending_urls": list(self.pending_urls)
        }
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro salvando checkpoint: {e}")

    def load_checkpoint(self):
        """Carrega estado do arquivo"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.visited_urls = set(data.get('visited_urls', []))
                    self.pending_urls = set(data.get('pending_urls', []))
                print(f"Checkpoint carregado: {len(self.visited_urls)} visitadas, {len(self.pending_urls)} pendentes")
            except Exception as e:
                print(f"Erro carregando checkpoint: {e}")

    def get_stats(self) -> dict:
        """Retorna estatísticas"""
        return {
            "visited_count": len(self.visited_urls),
            "pending_count": len(self.pending_urls),
            "total_count": len(self.visited_urls) + len(self.pending_urls)
        }
