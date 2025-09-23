from prefect import flow


@flow(name="Extract PDF to Images")
def extract_pdf_to_images():
    ...