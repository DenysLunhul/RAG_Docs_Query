from pydantic import BaseModel


class Settings(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 50
    s3_bucket_name: str
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()