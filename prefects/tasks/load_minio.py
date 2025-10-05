from prefect import task
from minio import Minio

client = Minio()


@task(name="Load file from MinIO")
def load_file_from_minio(bucket: str, key: str):
    ...