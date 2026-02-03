import hashlib
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass
class TableEntity:
    """Representa uma entidade individual extraída de uma linha de tabela"""
    entity_type: str  # 'contato', 'curso', 'campus', etc.
    key_field: str    # Campo chave (ex: 'Unidade', 'Código')
    key_value: str    # Valor do campo chave (ex: 'Campus Teresina Central')
    attributes: Dict[str, str]  # Outros atributos da entidade
    source_url: str   # URL de origem
    table_context: str  # Contexto da tabela (título ou descrição)

    def to_semantic_text(self) -> str:
        """Converte entidade para texto semântico otimizado para ENEM"""

        if self.entity_type == 'cronograma_enem':
            evento = self.key_value
            data = self.attributes.get('Data', '') or self.attributes.get('Período', '')
            return f"Evento do cronograma do ENEM: {evento}. Data ou período: {data}."

        elif self.entity_type == 'competencia_redacao':
            competencia = self.key_value
            descricao = self.attributes.get('Descrição', '') or self.attributes.get('Descritor', '')
            return f"Competência da redação do ENEM: {competencia}. {descricao}"

        elif self.entity_type == 'estrutura_prova':
            area = self.key_value
            questoes = self.attributes.get('Questões', '')
            peso = self.attributes.get('Peso', '')
            partes = [f"Área do ENEM: {area}"]
            if questoes:
                partes.append(f"Número de questões: {questoes}")
            if peso:
                partes.append(f"Peso: {peso}")
            return ". ".join(partes) + "."

        elif self.entity_type == 'nota_minima':
            curso = self.key_value
            nota = self.attributes.get('Nota', '') or self.attributes.get('Pontuação', '')
            instituicao = self.attributes.get('Instituição', '')
            partes = [f"Nota mínima para o curso {curso} no ENEM"]
            if instituicao:
                partes.append(f"Instituição: {instituicao}")
            if nota:
                partes.append(f"Nota exigida: {nota}")
            return ". ".join(partes) + "."

        else:
            attrs_text = ". ".join([f"{k}: {v}" for k, v in self.attributes.items()])
            return f"{self.key_field}: {self.key_value}. {attrs_text}."
    


    def generate_hash(self) -> str:
        """Gera hash único baseado no conteúdo semântico"""
        content = f"{self.entity_type}|{self.key_field}|{self.key_value}|{str(sorted(self.attributes.items()))}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

class TableProcessor:
    """Processador de tabelas orientado a entidades"""

    def __init__(self):
            # Mapeamento de tipos de tabela baseado em headers e URL
            self.table_type_patterns = {
        'cronograma_enem': {
            'headers': [
                ['evento', 'data'],
                ['etapa', 'período']
            ]
        },

        'competencia_redacao': {
            'headers': [
                ['competência', 'descrição'],
                ['nível', 'descritor']
            ]
        },

        'estrutura_prova': {
            'headers': [
                ['área', 'questões'],
                ['disciplina', 'peso']
            ]
        },

        'nota_minima': {
            'headers': [
                ['curso', 'nota'],
                ['instituição', 'pontuação']
            ]
        }
    }


    def process_table_html(self, table_html: str, source_url: str = "", context: str = "") -> List[TableEntity]:
        """Processa tabela HTML e retorna lista de entidades"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(table_html, 'html.parser')
            table = soup.find('table')
            if not table:
                return []

            # Extrair dados estruturados
            table_data = self._parse_html_table(table)
            if not table_data:
                return []

            # Inferir tipo da tabela
            entity_type = self._infer_table_type(table_data['headers'], source_url)

            # Converter para entidades
            entities = self._table_to_entities(table_data, entity_type, source_url, context)

            return entities

        except Exception as e:
            print(f"Erro processando tabela HTML: {e}")
            return []

    def _parse_html_table(self, table) -> Optional[Dict]:
        """Parseia tabela HTML para estrutura de dados"""
        rows = table.find_all('tr')
        if not rows:
            return None

        # Extrair headers
        headers = self._extract_html_headers(table, rows[0])

        # Extrair dados
        data_rows = []
        for row in rows[1:]:  # Pular primeira linha se for header
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                # Só adicionar se não for uma linha vazia
                if any(cell.strip() for cell in row_data):
                    data_rows.append(row_data)

        if not data_rows:
            return None

        return {
            'headers': headers,
            'rows': data_rows
        }

    def _extract_html_headers(self, table, first_row) -> List[str]:
        """Extrai headers de tabela HTML"""
        # Tentar thead primeiro
        thead = table.find('thead')
        if thead:
            header_cells = thead.find_all(['th', 'td'])
            if header_cells:
                return [cell.get_text(strip=True) for cell in header_cells]

        # Se não há thead, usar primeira linha
        header_cells = first_row.find_all(['th', 'td'])
        if header_cells:
            headers = [cell.get_text(strip=True) for cell in header_cells]
            # Verificar se parece ser header
            if self._is_header_row(headers):
                return headers

        # Fallback: headers genéricos
        num_cols = len(first_row.find_all(['td', 'th']))
        return [f"Coluna {i+1}" for i in range(num_cols)]

    def _is_header_row(self, cells: List[str]) -> bool:
        """Verifica se linha parece ser header"""
        if not cells:
            return False

        # Headers geralmente não são numéricos
        numeric_count = sum(1 for cell in cells if cell.replace('.', '').replace(',', '').replace(' ', '').isdigit())
        return numeric_count / len(cells) < 0.5

    def _infer_table_type(self, headers: List[str], source_url: str) -> str:
        """Infere tipo da tabela baseado em headers e URL"""
        # Normalizar headers para comparação
        norm_headers = [h.lower().strip() for h in headers]

        # Verificar padrões de headers
        for entity_type, patterns in self.table_type_patterns.items():
            for header_pattern in patterns['headers']:
                if all(any(h in nh for nh in norm_headers) for h in header_pattern):
                    return entity_type

        return 'generic'

    def _table_to_entities(
        self,
        table_data: Dict,
        entity_type: str,
        source_url: str,
        context: str
    ) -> List[TableEntity]:

        entities = []
        headers = table_data['headers']
        rows = table_data['rows']

        current_group = None  # ✅ inicializado corretamente

        for row in rows:
            # Linha de agrupamento (ex: "Redação", "Linguagens", etc.)
            if len(row) == 1:
                current_group = row[0]
                continue

            if len(row) != len(headers):
                continue  # linha malformada

            # Criar atributos
            attributes = dict(zip(headers, row))

            # Contexto por URL (opcional)
            inferred = self._infer_program(source_url)
            if inferred:
                attributes["Contexto"] = inferred

            if current_group:
                attributes["Grupo"] = current_group

            key_field = headers[0] if headers else "Entidade"
            key_value = row[0] if row else ""

            # Validação mínima
            if not key_value or len(key_value.strip()) < 3:
                continue

            entity = TableEntity(
                entity_type=entity_type,
                key_field=key_field,
                key_value=key_value,
                attributes=attributes,
                source_url=source_url,
                table_context=context
            )

            entities.append(entity)

        return entities

    def entities_to_chunks(self, entities: List[TableEntity]) -> List[Dict[str, Any]]:
        """Converte entidades em chunks otimizados para embedding"""
        chunks = []

        for entity in entities:
            # Texto semântico para embedding
            semantic_text = entity.to_semantic_text()

            # Metadados estruturados
            metadata = {
                'entity_type': entity.entity_type,
                'key_field': entity.key_field,
                'key_value': entity.key_value,
                'source_url': entity.source_url,
                'table_context': entity.table_context,
                'attributes': entity.attributes
            }

            chunk = {
                'text': semantic_text,
                'hash': entity.generate_hash(),
                'metadata': metadata,
                'entity': entity  # Manter referência para debug/processamento adicional
            }

            chunks.append(chunk)

        return chunks

    def create_semantic_chunks(self, table_html: str, source_url: str = "", context: str = "") -> List[Dict[str, Any]]:
        """Método principal: processa tabela HTML e retorna chunks semânticos"""
        entities = self.process_table_html(table_html, source_url, context)
        return self.entities_to_chunks(entities)


    def _infer_program(self, source_url: str) -> str | None:
        url = source_url.lower()
        if 'redacao' in url:
            return 'competencia_redacao'
        if 'cronograma' in url or 'datas' in url:
            return 'cronograma_enem'
        if 'estrutura' in url:
            return 'estrutura_prova'
        if 'nota' in url:
            return 'nota_minima'
        return None