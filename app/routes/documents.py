from fastapi import Depends, APIRouter, UploadFile
from app.models.database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from app.services.parser import extract_text
from app.services.embeddings import get_embedding
from app.models.chunks import DocumentChunk
from app.services.storage import upload_to_storage, download_from_storage, delete_from_storage, list_files_in_storage

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


@router.get("/list")
async def list_documents():
    files = list_files_in_storage()
    return {"files": files}


@router.get("/read")
async def read_document(filename: str):
    file = download_from_storage(filename)
    return StreamingResponse(file, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename*=UTF-8''{filename}"
    })


@router.delete("/delete")
async def delete_document(filename: str):
    delete_from_storage(filename)
    return {"Message": "Deleted"}