from prefect import flow, task

from io import BytesIO
from PIL import Image
import fitz

from prefects.providers.minio import get_minio_client
from prefects.providers.labelstudio import get_label_studio_client


@task(
    name="pdfs-to-images-task",
    log_prints=True,
)
def pdfs_to_images_task(
    data: BytesIO,
) -> list[Image.Image]:
    images = []
    pdf_document = fitz.open(stream=data, filetype="pdf")

    for page_num, page in enumerate(pdf_document):
        print(f"Processing page {page_num + 1}/{len(pdf_document)}")

        pix = page.get_pixmap(dpi=300)  # tweak DPI for quality/speed
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        images.append(img)

    return images


@flow(
    name="extract-pdfs-to-images",
    log_prints=True
)
def extract_pdfs_to_images_flow():
    minio_client = get_minio_client()
    label_studio_client = get_label_studio_client()

    label_studio_client.projects.create()

    # 1. List PDF files in MinIO 'raw' bucket

    # 2. Use PyMuPDF to extract images from each PDF file

    # 3. Upload extracted images to Label Studio via its API


if __name__ == "__main__":
    extract_pdfs_to_images_flow()