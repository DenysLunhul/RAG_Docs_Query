from fastapi import Depends, APIRouter, UploadFile
from app.models.database import get_db
from sqlalchemy.orm import Session

from app.services.storage import upload_to_storage
from app.services.parser import extract_text
from app.services.embeddings import get_embedding
from app.models.chunks import DocumentChunk


router = APIRouter(prefix="/document")


@router.post("/upload")
async def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    file_bytes = await file.read()
    file_name = file.filename
    upload_to_storage(file_bytes, file_name)
    chunks = extract_text(file_bytes)
    for chunk in chunks:
        chunk_obj = DocumentChunk(
            filename=file.filename,
            chunk_text=chunk,
            embedding=get_embedding(chunk)
        )
        db.add(chunk_obj)

    db.commit()
    return {"message": "uploaded", "chunks": len(chunks)}

