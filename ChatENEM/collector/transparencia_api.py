import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ENEMPublicSources:
    """
    Coletor de dados públicos oficiais sobre o ENEM
    Fontes: INEP / MEC / Editais oficiais
    """
    def __init__(self):
        self.sources = [
            {
                "name": "Cronograma ENEM",
                "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem",
                "type": "html"
            },
            {
                "name": "Cartilha da Redação",
                "url": "https://download.inep.gov.br/educacao_basica/enem/downloads/2023/cartilha_do_participante_2023.pdf",
                "type": "pdf"
            }
        ]
                
        self.headers = {
            "User-Agent": "ChatENEM/1.0 (Educational Bot)",
            "Accept-Language": "pt-BR"
        }
    
    def fetch_sources(self) -> List[Dict]:
        """
        Retorna metadados das fontes públicas do ENEM
        O conteúdo real será processado pelo pipeline de scraping/documentos
        """
        results = []

        for source in self.sources:
            try:
                results.append({
                    "url": source["url"],
                    "title": source["name"],
                    "source": "INEP / MEC",
                    "content_type": source["type"]
                })
            except Exception as e:
                logger.error(f"Erro ao registrar fonte {source['name']}: {e}")

        return results