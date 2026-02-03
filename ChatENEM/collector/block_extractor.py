from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
import re
from urllib.parse import urljoin, urlparse

ENUM_RE = re.compile(
    r'^\s*(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII)\s*[–\-]',
    re.IGNORECASE
)


class LayoutDetector:
    """
    Detecta o tipo de layout da página enem baseado em padrões da URL,
    classes do body e elementos característicos
    """

    def detect_layout(self, soup: BeautifulSoup, url: str) -> str:
        """
        Detecta o layout da página

        Returns:
            'default',
            'DocumentByLine',
            'DBL_and_external_link',
            'area_do_estudante',
            'conselhoeditorial',
            'consulta_de_processos',
            'section',
            'mediacarousel',
            'anchor_link',
            'DBL_and_outstanding-header',
            'tile_default_and_outstanding_header'
        """

        print(url)
        
        # Verificar padrões na URL
        url_lower = url.lower()

        if url_lower in ["https://enem.edu.br", "https://enem.edu.br/", "https://enem.edu.br/angical", "https://enem.edu.br/campomaior", "https://enem.edu.br/cocal", "https://enem.edu.br/corrente", "https://enem.edu.br/dirceu", "https://enem.edu.br/floriano", "https://enem.edu.br/josedefreitas", "https://enem.edu.br/oeiras", "https://enem.edu.br/parnaiba", "https://enem.edu.br/paulistana", "https://enem.edu.br/pedroii", "https://enem.edu.br/picos", "https://enem.edu.br/pioix", "https://enem.edu.br/piripiri", "https://enem.edu.br/saojoao", "https://enem.edu.br/saoraimundononato", "https://enem.edu.br/teresinacentral", "https://enem.edu.br/teresinazonasul", "https://enem.edu.br/urucui", "https://enem.edu.br/valenca", "https://enem.edu.br/ppi/menu-ppi", "https://enem.edu.br/ppgem", "https://enem.edu.br/novoead", "https://enem.edu.br/a-instituicao/diretorias-sistemicas/gestao-de-pessoas/boletim-de-servico/2018-1", "https://enem.edu.br/a-instituicao/diretorias-sistemicas/gestao-de-pessoas/boletim-de-servico/2022-1", "https://enem.edu.br/area-do-servidor/seci", "https://enem.edu.br/ppgem/o-mestrado/corpo-docente", "https://enem.edu.br/novoead/ensino-a-distancia-no-enem/institucional", "https://enem.edu.br/a-instituicao/avaliacao-institucional/regulamento-da-cpa", "https://enem.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis", "https://enem.edu.br/ppgem/processo-seletivo/selecao-2022-1", "https://enem.edu.br/a-instituicao/avaliacao-institucional/relatorios-de-autoavaliacao/2022", "https://enem.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis/demonstracoes-contabeis-e-notas-explicativas-1ot-2024", "https://enem.edu.br/conselho-editorial/membros", "https://enem.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/relatorios-de-gestao", "https://enem.edu.br/profmat", "https://enem.edu.br/acesso-a-informacao/licitacoes-e-contratos", "https://enem.edu.br/processos-seletivos/concursos", "https://enem.edu.br/area-do-estudante/tutoriais-suap-modulo-ensino", "https://enem.edu.br/ppgem/procedimento/normas-de-uso-dos-laboratorios", "https://enem.edu.br/acesso-a-informacao/governanca","https://enem.edu.br/a-instituicao/comissoes-e-comites/comite-de-governanca-institucional/plano-de-acao"] or ".pdf" in url_lower or url_lower.endswith("/o-campus") or "/receitas-proprias-e-despesas-por-sub-elementos/" in url_lower:
            # ajustar a extração da url: https://enem.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis
            return False


        if url_lower in ["https://enem.edu.br/a-instituicao/diretorias-sistemicas/diretoria-de-tecnologia-da-informacao/sistemas", "https://enem.edu.br/a-instituicao/diretorias-sistemicas/gestao-de-pessoas/boletim-de-servico", "https://enem.edu.br/a-instituicao/pro-reitorias", "https://ifpi.edu.br/a-instituicao/orgaos-colegiados", "https://ifpi.edu.br/a-instituicao/diretorias-sistemicas", "https://ifpi.edu.br/a-instituicao/comissoes-e-comites", "https://ifpi.edu.br/processos-seletivos", "https://ifpi.edu.br/acesso-a-informacao/gestao-de-riscos", "https://ifpi.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas", "https://ifpi.edu.br/acesso-a-informacao", "https://ifpi.edu.br/campi", "https://ifpi.edu.br/a-instituicao/campi", "https://ifpi.edu.br/a-instituicao", "https://ifpi.edu.br/area-do-estudante", "https://ifpi.edu.br/area-do-servidor", "https://ifpi.edu.br/lgpd", "https://ifpi.edu.br/cocal/o-campus/assistencia-estudantil/acoes-no-campus", "https://ifpi.edu.br/teresinacentral/o-campus/assistencia-estudantil", "https://ifpi.edu.br/servicos/transparencia-e-prestacao-de-contas", "https://ifpi.edu.br/a-instituicao/reitoria/reitor", "https://ifpi.edu.br/a-instituicao/reitoria/relacoes-internacionais", "https://ifpi.edu.br/a-instituicao/reitoria/gabinete-reitoria", "https://ifpi.edu.br/a-instituicao/reitoria/auditoria-interna", "https://ifpi.edu.br/a-instituicao/reitoria/cerimonial-eventos", "https://ifpi.edu.br/a-instituicao/reitoria/controladoria", "https://ifpi.edu.br/a-instituicao/reitoria/procuradoria-federal", "https://ifpi.edu.br/a-instituicao/reitoria/comunicacao/resolucoes-normativas",  "https://ifpi.edu.br/a-instituicao/reitoria/comunicacao/manuais-e-marcas", "https://ifpi.edu.br/a-instituicao/reitoria/comunicacao/midias-sociais", "https://ifpi.edu.br/autenticacao", "https://ifpi.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis/demonstracoes-contabeis-e-notas-explicativas-4ot-2024", "https://ifpi.edu.br/conselhoeditorial/publicacoes", "https://ifpi.edu.br/eleicoes2025/formulario", "https://ifpi.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis/2023", "https://ifpi.edu.br/a-instituicao/comissoes-e-comites/comite-de-governanca-institucional/eventos-tematicos", "https://ifpi.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis/2020", "https://ifpi.edu.br/a-instituicao/diretorias-sistemicas/gestao-de-pessoas/boletim-de-servico/2024-1", "https://ifpi.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis/2022", "https://ifpi.edu.br/acesso-a-informacao/transparencia-e-prestacao-de-contas/demonstracoes-contabeis/exercicio-2025", ""] or url_lower.endswith("/cursos") or "author" in url_lower:
            return 'DocumentByLine'
        

        if url_lower in ["https://ifpi.edu.br/area-do-servidor/psad", "https://ifpi.edu.br/psad", "https://ifpi.edu.br/area-do-servidor/psad/psad-rsad", "https://ifpi.edu.br/a-instituicao/comissoes-e-comites/comissao-interna-de-supervisao-do-plano-de-carreira-dos-cargos-tecnico-administrativos-em-educacao", "https://ifpi.edu.br/pdi-2025-2029"]:
            # DBL = DocumentByLine
            return 'DBL_and_external_link'

        
        if ("/area-do-estudante/" in url_lower or url_lower == "https://ifpi.edu.br/egressos") and not url_lower in ["https://ifpi.edu.br/area-do-estudante/bibliotecas/periodicos-eletronicos"] and not "/pro-reitorias/" in url_lower and not "/diretorias-sistemicas/" and not "/orgaos-colegiados/" in url_lower and not "/comissoes-e-comites/" in url_lower:
            return 'area_do_estudante'


        if (url_lower in ["https://ifpi.edu.br/conselhoeditorial", "https://ifpi.edu.br/mapeprof", "https://ifpi.edu.br/ppi",  "https://ifpi.edu.br/profmat", "https://ifpi.edu.br/mnpef", "https://ifpi.edu.br/autenticacao", "https://ifpi.edu.br/ead", "https://ifpi.edu.br/pgd", "http://ifpi.edu.br/ouvidoria", "http://ifpi.edu.br/cep", "https://ifpi.edu.br/ceua", "https://ifpi.edu.br/repensar", "https://ifpi.edu.br/pen-suap","https://ifpi.edu.br/pdi", "https://ifpi.edu.br/nit"] or "/view" in url_lower) and url_lower not in ["https://ifpi.edu.br/acesso-a-informacao/receitas-e-despesas/receitas-proprias-e-despesas-por-sub-elementos/receitas-proprias-e-despesas", "https://ifpi.edu.br/acesso-a-informacao/institucional/estrutura-organizacional"]:
            return 'conselhoeditorial'
        

        if url_lower in ["https://ifpi.edu.br/consulta-de-processos", "https://ifpi.edu.br/certificacao-do-ensino-medio", "https://ifpi.edu.br/area-do-estudante/bibliotecas/periodicos-eletronicos", "https://ifpi.edu.br/acesso-a-informacao/institucional/estrutura-organizacional", "https://ifpi.edu.br/acesso-a-informacao/receitas-e-despesas/receitas-proprias-e-despesas-por-sub-elementos/receitas-proprias-e-despesas", "https://ifpi.edu.br/ifpi-realiza-exame-classificatorio-2026.1", "https://ifpi.edu.br/novoead/ensino-a-distancia-no-ifpi/contatos", "https://ifpi.edu.br/educacao-a-distancia/rede-e-tec", "https://ifpi.edu.br/pdi/pdi-2020-2024/legislacao", "https://ifpi.edu.br/a-instituicao/reitoria"]:
            return 'consulta_de_processos'
        

        if "/noticias/" in url_lower:
            return 'section_and_photo-icon'
        

        if "repensar/" in url_lower:
            return 'mediacarousel'
        

        if url_lower in ["https://ifpi.edu.br/servicos/contatos"]:
            return 'anchor_link'


        if "/pro-reitorias/" in url_lower or "/diretorias-sistemicas/" in url_lower or "/orgaos-colegiados/" or "/comissoes-e-comites/" in url_lower or "/processos-seletivos/" or "/acesso-a-informacao/" in url_lower or url_lower.endswith("/assistencia-estudantil") or "/servicos/" in url_lower or url_lower in ["https://ifpi.edu.br/a-instituicao/reitoria/comunicacao"]:
                # DBL = DocumentByLine 
                return 'DBL_and_outstanding-header'
        
        if url_lower in ["https://ifpi.edu.br/profept"]:
            return 'tile-default_and_outstanding-header'
        
        if url_lower in ["https://ifpi.edu.br/processos-seletivos/sisu"]:
            # DBL = DocumentByLine, EL = external-link e IL = internal-link
            return 'DBL_and_EL_and_IL'
        
        if url_lower in ["https://ifpi.edu.br/eleicoes"]:
            # EL = external-link e IL = internal-link
            return 'outstanding-header_and_IL_and_EL'

        if url_lower in ["https://ifpi.edu.br/profept/coordenacao-academica-local"]:
            return 'callout_and_plain'
        
        if "noticias" in url_lower:
            return "listingBar"

        # Verificar classes do body
        # body = soup.find('body')
        # if body and body.get('class'):
        #     body_classes = ' '.join(body['class']).lower()
        #     if 'edital' in body_classes:
        #         return 'edital'
        #     if 'curso' in body_classes:
        #         return 'curso'
        #     if 'institucional' in body_classes:
        #         return 'institucional'

        # # Verificar elementos característicos
        # if soup.find('div', class_=re.compile(r'edital|concurs')):
        #     return 'edital'
        # if soup.find('div', class_=re.compile(r'curso|materia')):
        #     return 'curso'
        # if soup.find('div', class_=re.compile(r'institucional|about')):
        #     return 'institucional'

        return 'default'

class LayoutCleaner:
    """
    Interface base para limpeza contextual por layout
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        """
        Aplica limpeza específica do layout ao conteúdo principal
        """
        raise NotImplementedError

    def _apply_cleaning(self, main_content: BeautifulSoup, classes_to_remove: List[str]) -> BeautifulSoup:
        """
        Aplica a limpeza estrutural baseada nas regras fornecidas
        """
        # Criar uma cópia para não modificar o original
        cleaned_content = BeautifulSoup(str(main_content), 'html.parser')

        # Remover elementos por classe
        for class_name in classes_to_remove:
            if class_name:
                elements = cleaned_content.find_all(attrs={'class': re.compile(rf'\b{class_name}\b')})
                for element in elements:
                    element.decompose()

        ids_to_remove=['tile_banner_rotativo', 'viewlet-below-content-title']

        # Remover elementos por ID
        for id_name in ids_to_remove:
            if id_name:
                element = cleaned_content.find(id=id_name)
                if element:
                    element.decompose()

        return cleaned_content

class DefaultCleaner(LayoutCleaner):
    """
    Limpeza padrão - remove elementos genéricos de layout
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        # Classes a remover
        classes_to_remove = ["whatsapp", "documentByLine", "external-link", "callout", "photo-icon-pt-br photo-icon", "video-tile", "cover-collection-tile","outstanding-link", "tile-content",  "tileContent", "paginacao listingBar"]

        return self._apply_cleaning(main_content, classes_to_remove)


class documentByLineCleaner(LayoutCleaner):
    """
    Limpeza específica da class DocumentByLine
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["DocumentByLine"]

        return self._apply_cleaning(main_content, classes_to_remove)


class DBL_and_external_linkCleaner(LayoutCleaner):
    """
    Limpeza específica das class DocumentByLine e external-linkCleaner
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["DocumentByLine", "external-linkCleaner"]

        return self._apply_cleaning(main_content, classes_to_remove)


class area_do_estudanteCleaner(LayoutCleaner):
    """
    Limpeza específica para páginas da area do estudande e entre outras
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ['whatsapp', "documentByLine", "external-link", "callout", "photo-icon-pt-br photo-icon", "video-tile", "cover-collection-tile","outstanding-link", "outstanding-title"]

        return self._apply_cleaning(main_content, classes_to_remove)


class conselhoeditorialCleaner(LayoutCleaner):
    """
    Limpeza específica para páginas do conselho editorial e entre outras
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["whatsapp", "documentByLine", "callout", "photo-icon-pt-br photo-icon", "video-tile", "cover-collection-tile","outstanding-link", "outstanding-header"]

        return self._apply_cleaning(main_content, classes_to_remove)


class consulta_de_processosCleaner(LayoutCleaner):
    """
    Limpeza específica para páginas de consulta de processos e entre outras
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["whatsapp", "documentByLine", "photo-icon-pt-br photo-icon", "video-tile", "cover-collection-tile","outstanding-link", "tile-content",  "tileContent", "paginacao listingBar"]

        return self._apply_cleaning(main_content, classes_to_remove)


class section_and_photo_iconCleaner(LayoutCleaner):
    """
    Limpeza específica da class paginacao-listingBar
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["section", "photo-icon"]

        return self._apply_cleaning(main_content, classes_to_remove)


class mediacarouselCleaner(LayoutCleaner):
    """
    Limpeza específica da class mediacarousel
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["mediacarousel"]

        return self._apply_cleaning(main_content, classes_to_remove)


class anchor_linkCleaner(LayoutCleaner):
    """
    Limpeza específica da class anchor-link
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["anchor-link"]

        return self._apply_cleaning(main_content, classes_to_remove)


class DBL_and_outstanding_headerCleaner(LayoutCleaner):
    """
    Limpeza específica das class DocumentByLine e outstanding-header
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["DocumentByLine", "outstanding-header"]

        return self._apply_cleaning(main_content, classes_to_remove)


class tile_default_and_outstanding_header(LayoutCleaner):
    """
    Limpeza específica das class tile-default e outstanding-header
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["tile-default", "outstanding-header"]

        return self._apply_cleaning(main_content, classes_to_remove)


class DBL_and_EL_and_IL(LayoutCleaner):
    """
    Limpeza específica das class documentByLine, external-link e internal-link
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["ducumentByLine", "external-link", "internal-link"]

        return self._apply_cleaning(main_content, classes_to_remove)


class outstanding_header_and_IL_and_EL(LayoutCleaner):
    """
    Limpeza específica das class outstanding-header, external-link e internal-link
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["outstanding-header", "external-link", "internal-link"]

        return self._apply_cleaning(main_content, classes_to_remove)


class callout_and_plain(LayoutCleaner):
    """
    Limpeza específica das class callout e plain
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["callout", "plain"]

        return self._apply_cleaning(main_content, classes_to_remove)
    

class listingBar(LayoutCleaner):
    """
    Limpeza específica das class listingBar
    """

    def clean(self, main_content: BeautifulSoup) -> BeautifulSoup:
        classes_to_remove = ["listingBar"]

        return self._apply_cleaning(main_content, classes_to_remove)


class SectionBuilder:
    """
    Mantém o estado hierárquico da leitura do HTML.
    Suporta headings reais e pseudoheaders temporários (terminados em ':').
    """

    def __init__(self):
        # Cada item: (level, text, kind)
        # kind ∈ {"persistent", "temporary"}
        self.context_stack = []

    def update_context(
        self,
        heading_tag: str,
        heading_text: str,
        kind: str = "persistent"
    ):
        """
        Atualiza o contexto com um novo heading ou pseudoheader.

        - Headings reais (h1–h6) → kind="persistent"
        - Pseudoheader ':' → kind="temporary"
        """

        # Nível hierárquico
        if heading_tag.startswith("h") and heading_tag[1].isdigit():
            level = int(heading_tag[1])
        else:
            # pseudoheader textual
            level = 7  # abaixo de h6, mas acima de texto comum

        # Remove contextos do mesmo nível ou inferiores
        while self.context_stack and self.context_stack[-1][0] >= level:
            self.context_stack.pop()

        self.context_stack.append((level, heading_text, kind))

    def pop_temporary_context(self):
        """
        Remove pseudoheaders temporários do topo da pilha.
        """
        while self.context_stack and self.context_stack[-1][2] == "temporary":
            self.context_stack.pop()

    def get_current_context(self) -> Dict[str, str]:
        """
        Retorna o contexto hierárquico atual, incluindo pseudoheaders ativos.
        """
        context = {}
        for level, text, _kind in self.context_stack:
            key = f"h{level}" if level <= 6 else "pseudo"
            context[key] = text
        return context

    def reset(self):
        """
        Reseta o contexto (nova página).
        """
        self.context_stack = []

    def has_temporary_context(self) -> bool:
        return any(kind == "temporary" for _, _, kind in self.context_stack)


class BlockExtractor:
    """
    Extrator de blocos estruturados com preservação de contexto hierárquico
    """

    def __init__(self):
        self.layout_detector = LayoutDetector()
        self.section_builder = SectionBuilder()

        # Mapeamento de cleaners por layout
        self.cleaners = {
            'default': DefaultCleaner(),
            'DocumentByLine': documentByLineCleaner(),
            'DBL_and_external_link': DBL_and_external_linkCleaner(),
            'area_do_estudante': area_do_estudanteCleaner(),
            'conselhoeditorial': conselhoeditorialCleaner(),
            'consulta_de_processos': consulta_de_processosCleaner(),
            'section_and_photo-icon': section_and_photo_iconCleaner(),
            'mediacarousel': mediacarouselCleaner(),
            'anchor_link': anchor_linkCleaner(),
            'DBL_and_outstanding-header': DBL_and_outstanding_headerCleaner(),
            'tile-default_and_outstanding-header': tile_default_and_outstanding_header(),
            'DBL_and_EL_and_IL': DBL_and_EL_and_IL(),
            'outstanding-header_and_IL_and_EL': outstanding_header_and_IL_and_EL(),
            'callout_and_plain': callout_and_plain(),
            'listingBar': listingBar()
        }

        self.supported_tags = {
            'text_block': ['p', 'a', 'strong'],
            'list_block': ['ul', 'ol'],
            'table_block': ['table'],
            'iframe_block': ['iframe']
        }

        self.campus = [
            ["angical", "Angical"], 
            ["cocal", "Cocal"],
            ["dirceu" ,"Dirceu Arcoverde"],
            ["josedefreitas", "José de Freitas"],
            ["parnaiba", "Parnaíba"],
            ["pedroii", "Pedro II"],
            ["pioix", "Pio IX"],
            ["saojoao", "São João"],
            ["teresinacentral", "Teresina Central"],
            ["urucui", "Uruçuí"],
            ["campomaior", "Campo Maior"],
            ["corrente", "Corrente"],
            ["floriano", "Floriano"],
            ["oeiras", "Oeiras"],
            ["paulistana", "Paulistana"],
            ["picos", "Picos"],
            ["piripiri", "Piripiri"],
            ["saoraimundononato", "São Raimundo Nonato"],
            ["teresinazonasul", "Teresina Zona Sul"],
            ["valencia", "Valença"]
]

    def extract_blocks(self, html: str, base_url: str) -> Dict[str, Any]:
        """
        Extrai blocos estruturados com contexto hierárquico

        Args:
            html: Conteúdo HTML da página
            base_url: URL base para resolver links relativos

        Returns:
            {
                'url': base_url,
                'title': str,
                'blocks': List[Dict]
            }
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Resetar contexto para nova página
        self.section_builder.reset()

        # Extrair título
        title = self._extract_title(soup)

        # Detectar layout
        layout = self.layout_detector.detect_layout(soup, base_url)
        print(f"Layout detectado: {layout}")

        if not layout:

            # Extrair links para próximas URLs
            links = self._extract_links(soup, base_url)

            return {
            'url': base_url,
            'title': title,
            'blocks': [],
            'links': links
        }

    

        # Encontrar conteúdo principal
        main_content = self._find_main_content(soup)


        # Aplicar limpeza contextual por layout
        cleaned_content = self.cleaners[layout].clean(main_content)
        print(f"Conteúdo limpo aplicado para layout {layout}")


        # Extrair blocos com contexto hierárquico
        blocks = self._extract_blocks_with_context(cleaned_content, base_url, title)

        # Extrair links para próximas URLs
        links = self._extract_links(soup, base_url)

        return {
            'url': base_url,
            'title': title,
            'blocks': blocks,
            'links': links
        }

    def _extract_blocks_with_context(
        self,
        content: BeautifulSoup,
        base_url: str,
        title: str
    ) -> List[Dict]:
        """
        Extrai blocos com contexto hierárquico através de traversal sequencial,
        evitando duplicação de texto e respeitando precedência estrutural.
        """

        from bs4 import Tag

        blocks = []
        bloco = ""
        skip_parents = set()

        for i in self.campus:
            if i[0] in base_url:
                self.section_builder.update_context(
                    "h0",
                    "Conteúdo sobre o campus " + i[1],
                    kind="persistent"
                )


        # Traversia sequencial em ordem de documento
        for element in content.descendants:

            # 1. Só processa Tags reais
            if not isinstance(element, Tag):
                continue

            # 2. Ignora qualquer elemento cujo ancestral já foi consumido
            if any(parent in skip_parents for parent in element.parents):
                continue

            tag_name = element.name
            classes = element.get("class", [])

            # 3. Bloqueio semântico: nada dentro de table vira texto narrativo
            if element.find_parent("table"):
                continue

            # 4. Headings e callout atualizam contexto
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] or "callout" in classes:
                self.section_builder.pop_temporary_context()
                heading_text = self._clean_text(
                    element.get_text(separator=' ', strip=True)
                )
                if heading_text:
                    self.section_builder.update_context(tag_name, heading_text)
                    bloco += "\n" + heading_text
                    print(tag_name, heading_text)
                    skip_parents.add(element)
                continue

            current_context = self.section_builder.get_current_context()
            tag_pai = element.parent.name if element.parent else None

            # 5. DIV plana ou callout: consome tudo de uma vez
            if tag_name == 'div':
                block_tags = ['p', 'ul', 'ol', 'table',
                            'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

                if element.find(block_tags) is None:
                    text = self._clean_text(
                        element.get_text(separator=' ', strip=True)
                    )
                    if text:
                        bloco += "\n" + text
                        print(tag_name, text)
                        skip_parents.add(element)
                    continue

            # 6. Text blocks normais (p, span, etc.)
            if (
                tag_name in self.supported_tags['text_block']
                and tag_pai not in self.supported_tags['text_block']
            ):
                
                text = self._clean_text(
                    element.get_text(separator=' ', strip=True)
                )

                if not text:
                    continue

                # Fecha pseudoheader se o texto NÃO for enumeração
                if self.section_builder.has_temporary_context():
                    if not self._is_enumeration_paragraph(text):
                        text_block = self._create_text_block(
                        bloco,
                        base_url,
                        current_context if current_context else title
                    )
                    if text_block:
                        self.section_builder.pop_temporary_context()
                        blocks.append(text_block)
                        bloco = ""

                #  PSEUDOHEADER TEMPORÁRIO
                if self._is_temporary_pseudoheader(text):
                    self.section_builder.update_context(
                        heading_tag="pseudo",
                        heading_text=text,
                        kind="temporary"
                    )
                    print("PSEUDOHEADER:", text)
                    skip_parents.add(element)
                    continue

                #  TEXTO NORMAL
                bloco += "\n" + text
                print(tag_name, text)
                skip_parents.add(element)
                continue


            # 7. Listas
            if tag_name in self.supported_tags['list_block']:
                block = self._create_list_block(
                    element, base_url, current_context
                )
                if block:
                    text_block = self._create_text_block(
                        bloco,
                        base_url,
                        current_context if current_context else title
                    )
                    if text_block:
                        self.section_builder.pop_temporary_context()
                        blocks.append(text_block)
                        bloco = ""
                    blocks.append(block)
                continue

            # 8. Tabelas
            if (
                tag_name in self.supported_tags['table_block']
                and base_url != "https://ifpi.edu.br/a-instituicao/comissoes-e-comites/cppd"
            ):
                block = self._create_table_block(
                    element, base_url, current_context
                )
                if block:
                    text_block = self._create_text_block(
                        bloco,
                        base_url,
                        current_context if current_context else title
                    )
                    if text_block:
                        self.section_builder.pop_temporary_context()
                        blocks.append(text_block)
                        bloco = ""
                    blocks.append(block)
                    skip_parents.add(element)
                continue

            # 9. Iframes
            if tag_name in self.supported_tags['iframe_block']:
                block = self._create_iframe_block(
                    element, base_url, current_context
                )
                if block:
                    text_block = self._create_text_block(
                        bloco,
                        base_url,
                        current_context if current_context else title
                    )
                    if text_block:
                        blocks.append(text_block)
                        bloco = ""
                    blocks.append(block)
                continue

        # 10. Flush final
        if bloco:
            block = self._create_text_block(
                bloco,
                base_url,
                current_context if current_context else title
            )
            if block:
                blocks.append(block)

        return blocks


    def _create_text_block(self, text: str, base_url: str, context: dict[str, str]) -> Optional[Dict]:
        """Cria bloco de texto com contexto"""
        if not text:
            return None
        
        return ({
            'type': 'text_block',
            'content': text,
            'context': context,
            'metadata': {
                "atomic": self.section_builder.has_temporary_context(),
                'source_url': base_url,
                'confidence': 'high'
            }
        })

    def _create_list_block(self, element: Tag, base_url: str, context: Dict[str, str]) -> Optional[Dict]:
        """Cria bloco de lista com contexto"""
        items = []
        for li in element.find_all('li', recursive=False):
            item_text = self._clean_text(li.get_text())
            if item_text:
                items.append(item_text)

        if not items:
            return None

        list_type = 'ordered' if element.name == 'ol' else 'unordered'
        content = '\n'.join(f"• {item}" for item in items)

        return {
            'type': 'list_block',
            'content': content,
            'metadata': {
                'context': context,
                'list_type': list_type,
                'tag': element.name,
                'source_url': base_url,
                'confidence': 'high'
            }
            
        }

    def _create_table_block(self, element: Tag, base_url: str, context: Dict[str, str]) -> Optional[Dict]:
        """Cria bloco de tabela com contexto"""
        # Preservar HTML da tabela
        table_html = str(element)

        # Tentar extrair dados estruturados para metadados
        table_data = self._parse_table_structure(element)

        return {
            'type': 'table_block',
            'content': table_html,  # HTML bruto, não Markdown!
            'context': context,
            'table_data': table_data,
            'tag': 'table',
            'source_url': base_url,
            'confidence': 'high'
        }

    def _create_iframe_block(self, element: Tag, base_url: str, context: Dict[str, str]) -> Optional[Dict]:
        """Cria bloco de iframe com contexto"""
        src = element.get('src', '')
        if not src:
            return None

        # Resolver URL relativa
        full_src = urljoin(base_url, src)

        return {
            'type': 'iframe_block',
            'content': full_src,  # URL do iframe
            'context': context,
            'iframe_src': full_src,
            'tag': 'iframe',
            'source_url': base_url,
            'confidence': 'medium'  # Iframes podem ser bloqueados
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai título da página"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        return "Sem título"

    def _find_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Encontra o conteúdo principal da página"""
        # Priorizar tags semânticas
        main_candidates = [
            soup.find('article'),
            soup.find('div', id='content')
        ]

        for candidate in main_candidates:
            if candidate:
                return candidate

        # Fallback: body
        body = soup.find('body')
        return body if body else soup

    def _parse_table_structure(self, table: BeautifulSoup) -> Dict[str, Any]:
        """Parse estrutura da tabela para metadados"""
        headers = []
        rows = []

        # Headers
        header_elements = table.find_all('th')
        headers = [self._clean_text(th.get_text()) for th in header_elements]

        # Rows
        for tr in table.find_all('tr'):
            row_data = []
            for td in tr.find_all('td'):
                row_data.append(self._clean_text(td.get_text()))
            if row_data:
                rows.append(row_data)

        return {
            'headers': headers,
            'rows': rows,
            'columns': len(headers) if headers else (len(rows[0]) if rows else 0)
        }

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extrai todas as URLs de links da página"""
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()

            # Resolver URL relativa
            full_url = urljoin(base_url, href)

            # Filtrar âncoras e links externos se necessário
            parsed = urlparse(full_url)
            if parsed.fragment:  # Ignorar âncoras
                continue

            links.append(full_url)

        return links

    def _clean_text(self, text: str) -> str:
        """Limpa texto removendo espaços extras e quebras de linha"""
        if not text:
            return ""

        # Remover múltiplos espaços
        text = re.sub(r'\s+', ' ', text)

        # Remover espaços no início/fim
        text = text.strip()

        return text

    def _is_temporary_pseudoheader(self, text: str) -> bool:
        text = text.strip()

        if not text.endswith(":"):
            return False

        if len(text) < 25:
            return False

        # evitar lixo
        blacklist = ["http", "www", "@", "email"]
        if any(b in text.lower() for b in blacklist):
            return False

        return True

    def _is_enumeration_paragraph(self, text: str) -> bool:
        return bool(ENUM_RE.match(text.strip()))
