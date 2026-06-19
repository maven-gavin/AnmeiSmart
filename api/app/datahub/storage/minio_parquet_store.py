from typing import Optional

from app.core.minio_client import get_minio_client


class MinioParquetStore:
    def __init__(self, bucket: Optional[str] = None):
        self.minio = get_minio_client()
        self.bucket = bucket or self.minio.bucket_name

    def put_bytes(self, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        return self.minio.upload_file_data(object_name=object_key, file_data=data, content_type=content_type)

    def exists(self, object_key: str) -> bool:
        return self.minio.file_exists(object_name=object_key)

    def get_bytes(self, object_key: str) -> bytes:
        return self.minio.get_object_bytes(object_name=object_key)
