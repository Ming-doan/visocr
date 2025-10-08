from io import BytesIO
from typing import TypedDict
from logging import Logger, LoggerAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed

from prefect import task, get_run_logger
from minio import Minio
from minio.error import S3Error

from providers.minio import get_minio_client


class FileToUpload(TypedDict):
    object_name: str
    data: bytes
    content_type: str | None


def upload_object(
    client: Minio,
    bucket_name: str, file: FileToUpload,
    logger: Logger | LoggerAdapter
) -> str | None:
    minio_client = get_minio_client()

    try:
        logger.debug(f"Uploading {file['object_name']} to bucket '{bucket_name}'")
        stream = BytesIO(file["data"])
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=file["object_name"],
            data=stream,
            length=len(file["data"]),
            content_type=file["content_type"] or "application/octet-stream",
        )
        logger.debug(f"Uploaded {file['object_name']} to bucket '{bucket_name}'")
        return file["object_name"]
    except (S3Error, Exception) as e:
        logger.error(f"Failed to upload '{file['object_name']}': {e}")
        return None


@task(name="minio_upload_file_task", log_prints=True)
def upload_file_task(bucket_name: str, file: FileToUpload) -> str:
    """
    Prefect task: Upload a single file to a MinIO bucket.
    """
    minio_client = get_minio_client()
    logger = get_run_logger()

    obj_name = upload_object(minio_client, bucket_name, file, logger)
    if obj_name is None:
        raise RuntimeError(f"Upload failed for '{file['object_name']}' to '{bucket_name}'")

    logger.info(f"✅ Uploaded {file['object_name']} to bucket {bucket_name} complete.")
    return obj_name


@task(name="minio_upload_files_task", log_prints=True)
def upload_files_task(bucket_name: str, files: list[FileToUpload], max_workers: int = 5) -> list[str]:
    """
    Prefect task: Upload multiple files to a MinIO bucket in parallel.
    """
    minio_client = get_minio_client()
    logger = get_run_logger()

    total_files = len(files)
    logger.info(f"🚀 Uploading {total_files} files to '{bucket_name}' with {max_workers} workers...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(upload_object, minio_client, bucket_name, file, logger): file['object_name']
            for file in files
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    logger.info(f"✅ Upload complete — {len(results)}/{total_files} successful.")
    return results
