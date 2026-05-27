import pypdf
from app.config import settings

def extract_text(filename: str):
    """Extract text chunks from PDF"""
    reader = pypdf.PdfReader(filename)
    chunks = []
    chunk = ""
    next_chunk = ""
    chunk_size = 0
    for page in reader.pages:
        text = page.extract_text()
        words = text.split()
        for word in words:
            if chunk_size < settings.chunk_size:
                if chunk_size >= settings.chunk_size - settings.chunk_overlap:
                    next_chunk += f" {word}"
                chunk += f" {word}"
                chunk_size += 1
            else:
                chunk_size = 0
                chunks.append(chunk)
                chunk = next_chunk
                next_chunk = ""
    if chunk:
        chunks.append(chunk)
    return chunks