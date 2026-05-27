from io import BytesIO
import boto3
from app.config import settings

client = boto3.client('s3', region_name='us-east-1')

def upload_to_storage(file_bytes: bytes, filename: str) -> None:
    client.upload_fileobj(BytesIO(file_bytes), settings.s3_bucket_name, filename)

def delete_from_storage(filename: str) -> None:
    client.delete_object(Bucket=settings.s3_bucket_name, Key=filename)

def download_from_storage(filename) -> BytesIO:
    buffer = BytesIO()
    client.download_fileobj(settings.s3_bucket_name, filename, buffer)
    buffer.seek(0)
    return buffer