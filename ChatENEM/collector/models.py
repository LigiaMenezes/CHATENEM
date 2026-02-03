from django.db import models


class Document(models.Model):
    """Modelo para armazenar documentos coletados pelo crawler."""
    id = models.BigAutoField(primary_key=True)
    title = models.TextField(null=True, blank=True)
    source = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    url_norm = models.TextField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents"

    def __str__(self):
        return self.title or f"Document {self.id}"


class DocumentChunk(models.Model):
    """Modelo para armazenar chunks de texto dos documentos."""
    id = models.BigAutoField(primary_key=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_text = models.TextField()
    chunk_hash = models.CharField(max_length=128, unique=True)
    embedding_model = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_chunks"

    def __str__(self):
        return f"Chunk {self.id} (doc={self.document_id})"