import requests
import time
from typing import Optional, Dict, Any
import urllib.robotparser
from urllib.parse import urlparse

INSECURE_SSL_DOMAINS = {
    "inep.gov.br",
    "www.inep.gov.br",
    "gov.br",
    "www.gov.br",
    "mec.gov.br",
    "www.mec.gov.br",
    "ifpi.edu.br",
    "www.ifpi.edu.br",
}

class HTTPClient:
    """
    Cliente HTTP com retry, backoff, robots.txt e configuração avançada
    """

    def _is_insecure_domain(self, url: str) -> bool:
        host = urlparse(url).hostname
        return host in INSECURE_SSL_DOMAINS


    def __init__(
                self,
                user_agent: str = "ChatENEM/1.0 (Educational Research Bot - ENEM/INEP)",
                timeout: int = 30,
                max_retries: int = 3,
                backoff_factor: float = 2.0,
                respect_robots: bool = True
               ):

        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.respect_robots = respect_robots

        # Cache de robots.txt
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

        # Sessão requests com configurações otimizadas
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def can_fetch(self, url: str) -> bool:
        """Verifica se pode fazer fetch da URL (robots.txt)"""
        if not self.respect_robots:
            return True

        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            # Cache robots.txt
            if robots_url not in self.robots_cache:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                except:
                    # Se não conseguir ler, assume permissivo
                    pass
                self.robots_cache[robots_url] = rp

            rp = self.robots_cache[robots_url]
            return rp.can_fetch(self.user_agent, url)

        except Exception as e:
            print(f"Erro verificando robots.txt para {url}: {e}")
            return True  # Permissivo em caso de erro

    def fetch(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Faz requisição HTTP segura e controlada.

        Retorna:
            {
                status_code,
                content,
                headers,
                url,
                error
            }
        """

        # Verificar robots.txt
        if not self.can_fetch(url):
            return {
                'status_code': 403,
                'content': '',
                'headers': {},
                'url': url,
                'error': 'Blocked by robots.txt'
            }

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                print(f"Fetch attempt {attempt + 1}/{self.max_retries + 1}: {url}")

                insecure_ssl = self._is_insecure_domain(url)

                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=not insecure_ssl
                )

                if insecure_ssl:
                    print(f"[SSL INSEGURO - WHITELIST] {url}")


                # Sucesso
                if response.status_code == 200:
                    return {
                        'status_code': response.status_code,
                        'content': response.text,
                        'headers': dict(response.headers),
                        'url': response.url,
                        'error': None
                    }

                # Erro HTTP
                else:
                    return {
                        'status_code': response.status_code,
                        'content': response.text if response.text else '',
                        'headers': dict(response.headers),
                        'url': response.url,
                        'error': f'HTTP {response.status_code}'
                    }

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    print(f"Erro na tentativa {attempt + 1}: {e}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Falhou após {self.max_retries + 1} tentativas: {e}")

        # Todas as tentativas falharam
        return {
            'status_code': 0,
            'content': '',
            'headers': {},
            'url': url,
            'error': str(last_exception)
        }

    def close(self):
        """Fecha sessão"""
        self.session.close()
