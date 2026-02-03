from typing import List, Dict, Any, Optional
import requests
import tempfile
import os
import re

# Imports opcionais para processamento de documentos
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import easyocr
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

class DocumentProcessor:
    """
    Processa documentos incorporados (PDF, DOC, RAR, etc.)
    """

    def __init__(self):
        self.ocr_reader = None
        if HAS_OCR:
            try:
                self.ocr_reader = easyocr.Reader(['pt', 'en'], gpu=False)
            except Exception as e:
                print(f"Erro inicializando OCR: {e}")

    def process_document_url(self, url: str, container_url: str = "", container_type: str = "") -> List[Dict[str, Any]]:
        """
        Processa documento de uma URL

        Args:
            url: URL do documento
            container_url: URL da página que contém o documento
            container_type: Tipo do container (rar, zip, etc.)

        Returns:
            Lista de blocos de documento
        """
        try:
            # Download do documento
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Salvar temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_file_extension(url)) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_path = temp_file.name

            try:
                # Processar baseado no tipo
                doc_type = self._get_document_type(url)

                if doc_type == 'pdf':
                    blocks = self._process_pdf(temp_path, url)
                elif doc_type == 'docx':
                    blocks = self._process_docx(temp_path, url)
                elif doc_type in ['rar', 'zip']:
                    blocks = self._process_archive(temp_path, url)
                else:
                    blocks = []

                # Adicionar metadados do container
                for block in blocks:
                    block['container_url'] = container_url
                    block['container_type'] = container_type

                return blocks

            finally:
                # Limpar arquivo temporário
                os.unlink(temp_path)

        except Exception as e:
            print(f"Erro processando documento {url}: {e}")
            return [{
                'type': 'document_block',
                'content': f"Erro processando documento: {str(e)}",
                'source_type': 'error',
                'confidence': 'low',
                'error': str(e)
            }]

    def _get_document_type(self, url: str) -> str:
        """Determina tipo do documento pela URL"""
        url_lower = url.lower()

        if url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.docx', '.doc')):
            return 'docx'
        elif url_lower.endswith(('.rar', '.zip')):
            return 'rar'
        else:
            return 'unknown'

    def _get_file_extension(self, url: str) -> str:
        """Extrai extensão do arquivo da URL"""
        import os.path
        _, ext = os.path.splitext(url)
        return ext

    def _process_pdf(self, file_path: str, source_url: str) -> List[Dict[str, Any]]:
        """Processa arquivo PDF"""
        if not HAS_FITZ:
            return [{
                'type': 'document_block',
                'content': "PyMuPDF não instalado - não é possível processar PDFs",
                'source_type': 'pdf',
                'confidence': 'low'
            }]

        blocks = []

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Tentar extrair texto nativo
                text = page.get_text()

                if text.strip():
                    # Texto nativo encontrado
                    blocks.append({
                        'type': 'document_block',
                        'content': text.strip(),
                        'source_type': 'pdf',
                        'page': page_num + 1,
                        'confidence': 'high',
                        'extraction_method': 'native_text'
                        
                    })
                else:
                    # Tentar OCR se disponível
                    if self.ocr_reader and HAS_OCR:
                        try:
                            # Converter página para imagem
                            pix = page.get_pixmap()
                            img_path = f"{file_path}_page_{page_num}.png"
                            pix.save(img_path)

                            # OCR
                            results = self.ocr_reader.readtext(img_path, detail=0)
                            ocr_text = ' '.join(results)

                            if ocr_text.strip():
                                blocks.append({
                                    'type': 'document_block',
                                    'content': ocr_text.strip(),
                                    'source_type': 'pdf',
                                    'page': page_num + 1,
                                    'confidence': 'low',
                                    'extraction_method': 'ocr'
                                })

                            # Limpar imagem temporária
                            os.unlink(img_path)

                        except Exception as e:
                            print(f"Erro no OCR da página {page_num}: {e}")

            doc.close()

        except Exception as e:
            print(f"Erro processando PDF: {e}")

        return blocks

    def _process_docx(self, file_path: str, source_url: str) -> List[Dict[str, Any]]:
        """Processa arquivo DOCX"""
        if not HAS_DOCX:
            return [{
                'type': 'document_block',
                'content': "python-docx não instalado - não é possível processar DOCX",
                'source_type': 'docx',
                'confidence': 'low'
            }]

        blocks = []

        try:
            doc = docx.Document(file_path)

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    blocks.append({
                        'type': 'document_block',
                        'content': text,
                        'source_type': 'docx',
                        'confidence': 'high',
                        'extraction_method': 'native'
                    })

        except Exception as e:
            print(f"Erro processando DOCX: {e}")

        return blocks

    def _infer_enem_document_type(self, text: str) -> str:
        text_lower = text.lower()

        if "edital" in text_lower:
            return "edital"
        if "matriz de referência" in text_lower:
            return "matriz"
        if "prova objetiva" in text_lower:
            return "prova"
        if "gabarito" in text_lower:
            return "gabarito"
        if "competência" in text_lower and "redação" in text_lower:
            return "redacao"

        return "material_enem"


    def _process_archive(self, file_path: str, source_url: str) -> List[Dict[str, Any]]:
        """Processa arquivo RAR/ZIP (recursivo)"""
        blocks = []

        try:
            import zipfile

            with zipfile.ZipFile(file_path, 'r') as archive:
                for file_info in archive.filelist:
                    filename = file_info.filename

                    # Pular diretórios
                    if filename.endswith('/'):
                        continue

                    # Processar apenas documentos
                    if self._is_document_file(filename):
                        try:
                            # Extrair arquivo temporário
                            archive.extract(filename, os.path.dirname(file_path))
                            temp_doc_path = os.path.join(os.path.dirname(file_path), filename)

                            # Processar documento extraído
                            doc_blocks = self.process_document_url(
                                f"file://{temp_doc_path}",
                                source_url,
                                'archive'
                            )

                            # Adicionar nome do arquivo aos blocos
                            for block in doc_blocks:
                                block['archive_filename'] = filename

                            blocks.extend(doc_blocks)

                            # Limpar arquivo extraído
                            os.unlink(temp_doc_path)

                        except Exception as e:
                            print(f"Erro processando arquivo {filename} do archive: {e}")

        except Exception as e:
            print(f"Erro processando archive: {e}")

        return blocks

    def _is_document_file(self, filename: str) -> bool:
        """Verifica se arquivo é um documento processável"""
        doc_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
        return any(filename.lower().endswith(ext) for ext in doc_extensions)
