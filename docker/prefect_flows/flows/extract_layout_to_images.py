import os
from typing import TypedDict
import json
from io import BytesIO
from PIL import Image
import uuid

from prefect import flow, get_run_logger

from providers.config import get_default_configs, FlowConfig
from tasks.minio_download_files import download_files_task, download_file_task
from tasks.minio_upload_files import upload_files_task, FileToUpload


FLOW_NAME = "extract_layout_to_images"


class LayoutAnnotatedResult(TypedDict):
    image: Image.Image
    labels: list[str]
    x: float
    y: float
    width: float
    height: float


@flow(name=FLOW_NAME)
def extract_layout_to_images_flow(configs: FlowConfig | None = None) -> None:
    configs = configs or get_default_configs(FLOW_NAME)
    logger = get_run_logger()

    # 1. Download annotations from MinIO bucket
    annotations = download_files_task(
        bucket_name=f"{configs.get('source_folder', 'raw')}-annotated",
        max_workers=5
    )

    # 2. Read annotations as JSON
    annotations_data = [json.loads(ann.decode('utf-8')) for ann in annotations]

    # 3. Process annotations for each types
    layout_annotations: list[LayoutAnnotatedResult] = []
    for ann in annotations_data:
        # Get image path and check if exists
        image_path = ann.get("task", {}).get("data", {}).get("image")
        if not image_path:
            logger.warning(f"No image path found in annotation {ann.get('id')}. Skipping.")
            continue

        # Download image data from MinIO
        image_data = download_file_task(
            bucket_name=configs.get("source_folder", "raw"),
            object_name=os.path.basename(image_path)
        )

        # Convert image bytes to PIL Image
        image_data = Image.open(BytesIO(image_data)).convert("RGB")

        # Process results
        results = ann.get("result", [])
        for result in results:
            if result.get("type") != "rectanglelabels":
                continue

            labels = result.get("value", {}).get("rectanglelabels", None)
            if not labels:
                continue

            x = result.get("value", {}).get("x", None)
            y = result.get("value", {}).get("y", None)
            width = result.get("value", {}).get("width", None)
            height = result.get("value", {}).get("height", None)
            if None in (x, y, width, height):
                continue

            # Crop the image based on the bounding box
            original_width, original_height = image_data.size
            x = int((x / 100) * original_width)
            y = int((y / 100) * original_height)
            width = int((width / 100) * original_width)
            height = int((height / 100) * original_height)
            crop_box = (x, y, x + width, y + height)
            cropped_image = image_data.crop(crop_box)

            layout_annotations.append(LayoutAnnotatedResult(
                image=cropped_image,
                labels=labels,
                x=x,
                y=y,
                width=width,
                height=height
            ))
        logger.info(f"Processed {len(results)} results for image {image_path}")

        # Close the original image to free memory
        image_data.close()

    # 4. Save cropped images to respective folders based on labels
    ocr_images: list[FileToUpload] = []
    tableformer_images: list[FileToUpload] = []
    imagecaption_images: list[FileToUpload] = []

    for ann in layout_annotations:
        # Read image as bytes
        buffer = BytesIO()
        ann["image"].save(buffer, format="JPEG")
        buffer.seek(0)

        # Distribute images based on labels
        for label in ann["labels"]:
            if label in configs.get("filtered_ocr_labels", []):
                ocr_images.append(FileToUpload(
                    object_name=f"{uuid.uuid4()}.jpg",
                    data=buffer.getvalue(),
                    content_type="image/jpg"
                ))
            elif label in configs.get("filtered_tableformer_labels", []):
                tableformer_images.append(FileToUpload(
                    object_name=f"{uuid.uuid4()}.jpg",
                    data=buffer.getvalue(),
                    content_type="image/jpg"
                ))
            elif label in configs.get("filtered_imagecaption_labels", []):
                imagecaption_images.append(FileToUpload(
                    object_name=f"{uuid.uuid4()}.jpg",
                    data=buffer.getvalue(),
                    content_type="image/jpg"
                ))
            else:
                logger.warning(f"Unknown label '{label}' found. Skipping.")

        # Close the cropped image to free memory
        ann["image"].close()
        
    logger.info(f"Total cropped images - OCR: {len(ocr_images)}, TableFormer: {len(tableformer_images)}, ImageCaption: {len(imagecaption_images)}")

    # 5. Upload images to respective MinIO buckets
    if ocr_images:
        upload_files_task(
            bucket_name=configs.get("target_ocr_folder", "utils"),
            files=ocr_images,
            max_workers=5
        )
    # if tableformer_images:
    #     upload_files_task(
    #         bucket_name=configs.get("target_tableformer_folder", "utils"),
    #         files=tableformer_images,
    #         max_workers=5
    #     )
    # if imagecaption_images:
    #     upload_files_task(
    #         bucket_name=configs.get("target_imagecaption_folder", "utils"),
    #         files=imagecaption_images,
    #         max_workers=5
    #     )
    logger.info("✅ Extract layout to images flow completed.")