from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger, LoggerAdapter

from prefect import task, get_run_logger
from minio import Minio
from minio.error import S3Error

from providers.minio import get_minio_client


def download_object(
    client: Minio,
    bucket_name: str,
    object_name: str | None,
    logger: Logger | LoggerAdapter
) -> bytes | None:
    if object_name is None:
        return None

    try:
        logger.debug(f"Downloading {object_name} from bucket '{bucket_name}'")
        response = client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        logger.debug(f"Downloaded {object_name} successfully")
        return data
    except (S3Error, Exception) as e:
        logger.error(f"Failed to download '{object_name}': {e}")
        return None


@task(name="minio_download_file_task", log_prints=False)
def download_file_task(bucket_name: str, object_name: str) -> bytes:
    """
    Downloads a single file from a specified MinIO bucket.
    """
    minio_client = get_minio_client()
    logger = get_run_logger()

    data = download_object(minio_client, bucket_name, object_name, logger)
    if data is None:
        raise RuntimeError(f"Download failed for '{object_name}' in '{bucket_name}'")

    logger.info(f"✅ Download complete: {object_name}")
    return data


@task(name="minio_download_files_task", log_prints=False)
def download_files_task(
    bucket_name: str,
    filter_extensions: tuple[str] | None = None,
    max_workers: int = 5
) -> list[bytes]:
    """
    Downloads all files from a specified MinIO bucket in parallel.
    """
    logger = get_run_logger()
    minio_client = get_minio_client()

    # List all objects (recursive = include subfolders)
    objects = list(minio_client.list_objects(bucket_name, recursive=True))
    if filter_extensions:
        objects = [
            obj for obj in objects
            if obj.object_name and obj.object_name.lower().endswith(filter_extensions)
        ]
    logger.info(f"Found {len(objects)} files in bucket '{bucket_name}'")

    files_data: list[bytes] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_obj = {
            executor.submit(download_object, minio_client, bucket_name, obj.object_name, logger): obj
            for obj in objects
        }

        for future in as_completed(future_to_obj):
            data = future.result()
            if data:
                files_data.append(data)

    logger.info(f"✅ Successfully downloaded {len(files_data)} files from '{bucket_name}'")
    return files_data
