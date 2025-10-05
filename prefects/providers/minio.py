import os
from functools import lru_cache
from minio import Minio


@lru_cache(maxsize=1)
def get_minio_client():
    return Minio(
        endpoint="localhost:9000",
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False,
    )