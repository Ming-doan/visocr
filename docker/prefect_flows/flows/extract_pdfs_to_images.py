from PIL import Image
import uuid
from io import BytesIO

from prefect import flow

from providers.config import get_default_configs, FlowConfig
from tasks.minio_download_files import download_files_task
from tasks.pdfs_to_imgs import pdfs_to_imgs_task
from tasks.minio_upload_files import upload_files_task, FileToUpload


FLOW_NAME = "extract_pdfs_to_images"


@flow(name=FLOW_NAME)
def extract_pdfs_to_images_flow(configs: FlowConfig | None = None) -> None:
    configs = configs or get_default_configs(FLOW_NAME)

    # 1. List PDF files in MinIO bucket
    files = download_files_task(
        bucket_name=configs.get("source_folder", "raw"),
        filter_extensions=(".pdf",),
        max_workers=5
    )

    # 2. Use PyMuPDF to extract images from each PDF file
    pdf_imgs: list[Image.Image] = []
    for file_data in files:
        images = pdfs_to_imgs_task(data=file_data, dpi=300, max_pages=None)
        pdf_imgs.extend(images)

    # 3. Convert images to bytes and upload to MinIO bucket
    files_to_upload: list[FileToUpload] = []
    for img in pdf_imgs:
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        files_to_upload.append({
            "object_name": f"{uuid.uuid4()}.jpg",
            "data": buffer.getvalue(),
            "content_type": "image/jpg"
        })
    upload_files_task(
        bucket_name=configs.get("target_folder", "utils"),
        files=files_to_upload,
        max_workers=5
    )