from io import BytesIO
import boto3
from app.config import settings

s3 = boto3.client('s3', region_name='us-east-1')

def upload_to_storage(file_bytes: bytes, filename: str) -> None:
    s3.upload_fileobj(BytesIO(file_bytes), settings.s3_bucket_name, filename)

def delete_from_storage(filename: str) -> None:
    s3.delete_object(Bucket=settings.s3_bucket_name, Key=filename)

def list_files_in_storage() -> list[str]:
    response = s3.list_objects_v2(Bucket=settings.s3_bucket_name)
    if "Contents" not in response:
        return []
    return [obj["Key"] for obj in response["Contents"]]

def download_from_storage(filename) -> BytesIO:
    buffer = BytesIO()
    s3.download_fileobj(settings.s3_bucket_name, filename, buffer)
    buffer.seek(0)
    return buffer