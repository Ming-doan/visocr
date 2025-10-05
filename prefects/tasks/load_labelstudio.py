from prefect import task
from label_studio_sdk.client import LabelStudio


@task(name="Load project from Label Studio")
def load_project_from_label_studio(project_id: str):
    ...