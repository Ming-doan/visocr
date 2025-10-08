import os
from functools import lru_cache
from minio import Minio


APP_HOST = os.getenv("APP_HOST", "localhost")
MINIO_HOST = os.getenv("MINIO_HOST", APP_HOST)


@lru_cache(maxsize=1)
def get_minio_client():
    return Minio(
        endpoint=f"{MINIO_HOST}:9000",
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        secure=False,
    )