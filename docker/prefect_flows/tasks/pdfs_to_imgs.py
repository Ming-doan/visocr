from PIL import Image
import fitz # PyMuPDF
from prefect import task, get_run_logger


@task(name="pdfs_to_imgs_task", log_prints=False)
def pdfs_to_imgs_task(
    data: bytes,
    dpi: int = 300,
    max_pages: int | None = None,
) -> list[Image.Image]:
    """
    Converts each page of a PDF (in bytes) to a list of PIL Images.

    Args:
        data (bytes): The PDF file content.
        dpi (int): Resolution for rendering. Default is 300.
        max_pages (int | None): Limit number of pages to convert (for large PDFs).

    Returns:
        list[Image.Image]: List of images representing each page.
    """
    logger = get_run_logger()

    # Open PDF from memory
    try:
        pdf_document = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        logger.error(f"Failed to open PDF: {e}")

    total_pages = pdf_document.page_count
    logger.info(f"Opened PDF with {total_pages} pages (DPI={dpi}).")

    zoom_matrix = fitz.Matrix(dpi / 72, dpi / 72)
    images: list[Image.Image] = []

    try:
        for page_num in range(total_pages):
            if max_pages and page_num >= max_pages:
                logger.info(f"Stopping early at page {page_num} (max_pages={max_pages})")
                break

            page = pdf_document.load_page(page_num)
            logger.debug(f"Rendering page {page_num + 1}/{total_pages}")

            pix = page.get_pixmap(matrix=zoom_matrix)  # type: ignore[attr-defined]

            # Handle transparency correctly
            mode = "RGBA" if pix.alpha else "RGB"
            image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            image = image.convert("RGB")  # Ensure no alpha channel

            images.append(image)

        logger.info(f"✅ Converted {len(images)} pages to images.")
        return images

    finally:
        pdf_document.close()
