from fastapi import Depends, APIRouter, UploadFile
from app.models.database import get_db
from sqlalchemy.orm import Session

from app.models.schemas import Question
from app.services.rag import retrieve_chunks, generate_answer

router = APIRouter(prefix="/query")


@router.post("")
async def query(question: Question, db: Session = Depends(get_db)) -> str:
    chunks = retrieve_chunks(question.query, db)
    answer = generate_answer(question.query, chunks)
    return answer