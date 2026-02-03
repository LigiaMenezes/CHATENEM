from typing import List, Dict, Any
import hashlib
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .table_processor import TableProcessor

class SemanticProcessor:
    """
    Processa blocos estruturados em chunks semânticos atômicos
    """

    def __init__(self):
        self.table_processor = TableProcessor()

    def process_blocks_to_chunks(self, blocks, source_url):
        chunks = []

        for block in blocks:
            block_type = block.get("type")

            if block_type == "text_block":
                chunks.extend(self._process_text_block(block, source_url))

            elif block_type == "list_block":
                chunks.append(self._create_chunk(
                    text=block.get("content", ""),
                    chunk_type="text",
                    source_url=source_url,
                    source_type="html",
                    confidence="high",
                    metadata={
                        "entity_type": "educational_list"
                    }
                ))

            elif block_type == "table_block":
                chunks.extend(self._process_table_block(block, source_url))

            elif block_type == "iframe_block":
                chunks.extend(self._process_iframe_block(block, source_url))

            elif block_type == "document_block":
                chunks.extend(self._process_document_block(block, source_url))

        return chunks

    def _process_text_block(self, block, source_url):
        text = block.get("content", "").strip()
        if not text:
            return []

        metadata = block.get("metadata", {})
        atomic = metadata.get("atomic", False)
        context = block.get("context", {})

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", "; ", ", ", " "]
        )

        texts = [text] if atomic else splitter.split_text(text)

        chunks = []
        for t in texts:
            enriched_text = t

            if context:
                header = " > ".join(context.values())
                enriched_text = f"{header}\n{t}"

            chunks.append(self._create_chunk(
                text=enriched_text,
                chunk_type="text",
                source_url=source_url,
                source_type="html",
                confidence=metadata.get("confidence", "high"),
                metadata={
                    "entity_type": "enem_content",
                    "context": context
                }
            ))

        return chunks

    def _process_table_block(self, block: Dict, source_url: str) -> List[Dict[str, Any]]:
        """
        Processa bloco de tabela convertendo em entidades semânticas
        CRÍTICO: Uma linha da tabela = uma entidade = um chunk
        """
        table_html = block.get('content', '')
        table_data = block.get('table_data', {})

        if not table_html:
            return []

        try:
            # Usar TableProcessor para converter tabela em entidades
            entities = self.table_processor.process_table_html(table_html, source_url, "Tabela extraída")

            # Converter entidades em chunks
            chunks = []
            for entity in entities:
                semantic_text = entity.to_semantic_text()

                chunk = self._create_chunk(
                    text=semantic_text,
                    chunk_type='table_entity',
                    source_url=source_url,
                    source_type='html',
                    confidence=block.get('confidence', 'high'),
                    metadata={
                        'entity_type': entity.entity_type,
                        'key_field': entity.key_field,
                        'key_value': entity.key_value,
                        'attributes': entity.attributes,
                        'table_context': entity.table_context
                    }
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            print(f"Erro processando tabela: {e}")
            # Fallback: tratar como texto simples
            return self._process_text_block({
                'content': f"Tabela: {table_data}",
                'confidence': 'low'
            }, source_url)

    def _process_iframe_block(self, block: Dict, source_url: str) -> List[Dict[str, Any]]:
        """Processa bloco de iframe"""
        iframe_src = block.get('iframe_src', '')

        # Iframe vira um chunk informativo
        chunk = self._create_chunk(
            text=f"Conteúdo incorporado disponível em: {iframe_src}",
            chunk_type='text',
            source_url=source_url,
            source_type='iframe',
            confidence=block.get('confidence', 'medium'),
            metadata={
                'iframe_src': iframe_src,
                'entity_type': 'iframe'
            }
        )

        return [chunk]

    def _process_document_block(self, block: Dict, source_url: str) -> List[Dict[str, Any]]:
        """Processa bloco de documento (PDF, DOC, etc.)"""
        content = block.get('content', '')
        source_type = block.get('source_type', 'document')

        # Dividir conteúdo do documento em chunks
        text_chunks = self._split_into_sentences(content)

        chunks = []
        for text_chunk in text_chunks:
            if len(text_chunk.strip()) > 50:
                chunk = self._create_chunk(
                    text=text_chunk.strip(),
                    chunk_type='text',
                    source_url=source_url,
                    source_type=source_type,
                    confidence=block.get('confidence', 'high'),
                    metadata={
                        'page': block.get('page'),
                        'container_url': block.get('container_url'),
                        'container_type': block.get('container_type'),
                        'entity_type': 'document_text'
                    }
                )
                chunks.append(chunk)

        return chunks

    def _create_chunk(self, text: str, chunk_type: str, source_url: str,
                     source_type: str, confidence: str, metadata: Dict = None) -> Dict[str, Any]:
        """Cria chunk padronizado"""
        if metadata is None:
            metadata = {}

        # Gerar hash único
        chunk_hash = hashlib.sha256(f"{source_url}:{text}".encode('utf-8')).hexdigest()

        return {
            'hash': chunk_hash,
            'text': text,
            'metadata': {
                'type': chunk_type,
                'source_url': source_url,
                'source_type': source_type,
                'entity_type': metadata.get('entity_type', 'unknown'),
                'attributes': metadata.get('attributes', {}),
                'confidence': confidence,
                **metadata  # Incluir outros metadados
            }
        }

    def _split_into_sentences(self, text: str) -> List[str]:
        """Divide texto em sentenças semanticamente coerentes"""
        if not text:
            return []

        # Dividir por pontuação
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Filtrar sentenças muito curtas e muito longas
        filtered_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if 20 <= len(sentence) <= 1000:  # Limites razoáveis
                filtered_sentences.append(sentence)

        # Se não conseguiu dividir bem, dividir por parágrafos
        if len(filtered_sentences) < 2:
            paragraphs = text.split('\n\n')
            filtered_sentences = [p.strip() for p in paragraphs if 50 <= len(p.strip()) <= 2000]

        return filtered_sentences
