from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    chunk_size: int = 500
    chunk_overlap: int = 50
    s3_bucket_name: str
    database_url: str
    bedrock_model_id: str

    class Config:
        env_file = ".env"

settings = Settings()