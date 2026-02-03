from typing import List, Dict, Any
import time

from .url_manager import URLManager
from .http_client import HTTPClient
from .block_extractor import BlockExtractor
from .document_processor import DocumentProcessor
from .semantic_processor import SemanticProcessor
from .database_layer import DatabaseLayer


class ENEMScrapingPipeline:
    """
    Pipeline oficial de coleta e indexação de documentos do ENEM / INEP.

    Objetivo:
    - Coletar APENAS conteúdos públicos e oficiais
    - Converter páginas e documentos em conhecimento semântico
    - Alimentar o ChatENEM com base verificável
    """

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        domain_filter: str = "inep.gov.br",
        checkpoint_file: str = "ChatENEM/data/enem_scraping_checkpoint.json",
        max_pages: int = 200,
        delay: float = 1.5
    ):
        # Núcleo do pipeline
        self.url_manager = URLManager(checkpoint_file, domain_filter)
        self.http_client = HTTPClient(
            user_agent="ChatENEM/1.0 (Educational Research Bot - INEP/ENEM)"
        )
        self.block_extractor = BlockExtractor()
        self.document_processor = DocumentProcessor()
        self.semantic_processor = SemanticProcessor()
        self.database = DatabaseLayer(supabase_url, supabase_key)

        # Configurações
        self.max_pages = max_pages
        self.delay = delay
        self.domain_filter = domain_filter

        # Estatísticas
        self.stats = {
            "pages_processed": 0,
            "chunks_created": 0,
            "documents_processed": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    # =============================
    # PIPELINE PRINCIPAL
    # =============================

    def run(self, seed_urls: List[str]) -> Dict[str, Any]:
        print("=== Iniciando Pipeline Oficial do ChatENEM ===")
        self.stats["start_time"] = time.time()

        self.url_manager.add_seed_urls(seed_urls)
        print(f"URLs iniciais carregadas: {len(seed_urls)}")

        while self.stats["pages_processed"] < self.max_pages:
            url = self.url_manager.get_next_pending()

            if not url:
                print("Nenhuma URL pendente restante.")
                break

            print(f"\n🔍 Processando página {self.stats['pages_processed'] + 1}/{self.max_pages}")
            print(f"URL: {url}")

            success = self._process_page(url)

            if success:
                self.stats["pages_processed"] += 1
                time.sleep(self.delay)
            else:
                self.stats["errors"] += 1

            if self.stats["pages_processed"] % 10 == 0:
                self._print_progress()

        self.stats["end_time"] = time.time()
        self._print_final_stats()
        self.http_client.close()

        return self.stats

    # =============================
    # PROCESSAMENTO DE PÁGINA
    # =============================

    def _process_page(self, url: str) -> bool:
        try:
            response = self.http_client.fetch(url)

            if response["status_code"] != 200:
                print(f"Erro HTTP {response['status_code']}")
                return False

            html = response["content"]

            # 1. Extrair blocos da página
            page_data = self.block_extractor.extract_blocks(html, url)

            # 2. Processar documentos oficiais (PDFs, DOCs)
            document_blocks = self._process_embedded_documents(page_data)
            page_data["blocks"].extend(document_blocks)

            # 3. Descobrir novas URLs relevantes
            for link in page_data.get("links", []):
                self.url_manager.add_pending_url(link)

            # 4. Converter blocos em chunks semânticos
            chunks = self.semantic_processor.process_blocks_to_chunks(
                page_data["blocks"],
                url
            )

            # 5. Inserir documento + chunks
            doc_id = self.database.insert_document(
                url=url,
                title=page_data.get("title", "Documento ENEM"),
                source_type="enem_oficial"
            )

            if doc_id and chunks:
                result = self.database.insert_chunks(chunks, doc_id)
                self.stats["chunks_created"] += result["inserted"]

            self.url_manager.mark_visited(url)
            self.stats["documents_processed"] += 1

            print("✓ Página ENEM processada com sucesso")
            return True

        except Exception as e:
            print(f"Erro processando página ENEM: {e}")
            return False

    # =============================
    # DOCUMENTOS INCORPORADOS
    # =============================

    def _process_embedded_documents(self, page_data: Dict[str, Any]) -> List[Dict]:
        document_blocks = []

        for block in page_data.get("blocks", []):
            if block.get("type") == "text_block":
                urls = self._extract_document_urls(block.get("content", ""))

                for doc_url in urls:
                    print(f"📄 Documento oficial encontrado: {doc_url}")
                    try:
                        blocks = self.document_processor.process_document_url(
                            doc_url,
                            container_url=page_data.get("url"),
                            container_type="enem_page"
                        )
                        document_blocks.extend(blocks)
                    except Exception as e:
                        print(f"Erro ao processar documento ENEM: {e}")

        return document_blocks

    def _extract_document_urls(self, text: str) -> List[str]:
        import re
        patterns = [
            r"https?://[^\s]+\.pdf",
            r"https?://[^\s]+\.docx?",
            r"https?://[^\s]+\.zip",
        ]
        urls = []
        for p in patterns:
            urls.extend(re.findall(p, text, re.IGNORECASE))
        return list(set(urls))

    # =============================
    # LOGS E ESTATÍSTICAS
    # =============================

    def _print_progress(self):
        db = self.database.get_stats()
        urls = self.url_manager.get_stats()

        print("\n📊 Progresso ChatENEM")
        print(f"Páginas: {self.stats['pages_processed']}")
        print(f"Documentos: {db['documents']}")
        print(f"Chunks: {db['chunks']}")
        print(f"URLs pendentes: {urls['pending_count']}")
        print(f"Erros: {self.stats['errors']}")
        print("-" * 40)

    def _print_final_stats(self):
        elapsed = self.stats["end_time"] - self.stats["start_time"]

        print("\n" + "=" * 60)
        print("PIPELINE CHATENEM FINALIZADO")
        print("=" * 60)
        print(f"Tempo total: {elapsed:.1f}s")
        print(f"Páginas processadas: {self.stats['pages_processed']}")
        print(f"Documentos processados: {self.stats['documents_processed']}")
        print(f"Chunks criados: {self.stats['chunks_created']}")
        print(f"Erros: {self.stats['errors']}")
        print("=" * 60)
