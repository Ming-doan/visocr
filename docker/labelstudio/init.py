import os
import argparse
import json
from label_studio_sdk.client import LabelStudio

# --------------- Configuration ---------------

LABEL_STUDIO_URL = f"http://localhost:{os.getenv('LABEL_STUDIO_PORT', '8080')}"
CONFIG_PATH = "/configs/configs.json"

# ---------------------------------------------

parser = argparse.ArgumentParser(description="Initialize Label Studio project")
parser.add_argument("-t", "--token", type=str, required=True,
                    help="API token for Label Studio. Go to `{host}/user/account` to get your token.")


def create_project(
    ls: LabelStudio,
    configs: dict,
) -> int:
    # Check if the project already exists
    projects = ls.projects.list()
    if LABEL_STUDIO_INIT_PROJECT in [project.title for project in projects]:
        print(
            f"📦 Project '{LABEL_STUDIO_INIT_PROJECT}' already exists. Skipping creation.")
        return next((project.id for project in projects if project.title == LABEL_STUDIO_INIT_PROJECT), None)
    print(f"📦 Creating project '{LABEL_STUDIO_INIT_PROJECT}'...", end=" ")

    # Load the label config from the file
    with open(LABEL_STUDIO_CONFIG_PATH, "r") as file:
        label_config = file.read()

    # Create the project with the label config
    project = ls.projects.create(
        title=LABEL_STUDIO_INIT_PROJECT,
        label_config=label_config
    )
    print(f"Project '{LABEL_STUDIO_INIT_PROJECT}' created successfully.")

    return project.id


# Check if the storage already exists
def create_storage(ls: LabelStudio, project_id: int) -> int:
    storages = ls.import_storage.local.list(project=project_id)
    if LABEL_STUDIO_INIT_PROJECT in [storage.title for storage in storages]:
        print(
            f"📦 Storage '{LABEL_STUDIO_INIT_PROJECT}' already exists. Skipping creation.")

        storage = next(
            (storage for storage in storages if storage.title == LABEL_STUDIO_INIT_PROJECT), None)
    else:
        # Connect to local file storage
        print(f"📦 Creating storage '{LABEL_STUDIO_INIT_PROJECT}'...", end=" ")
        storage = ls.import_storage.local.create(
            title=LABEL_STUDIO_INIT_PROJECT,
            project=project_id,
            path=LABEL_STUDIO_FILE_PATH,
            regex_filter=".*\.(jpg|jpeg|png|gif|webp|jfif)$",
            use_blob_urls=True,
        )
        print(f"Storage '{LABEL_STUDIO_INIT_PROJECT}' created successfully.")

    # Sync the storage to ensure it's ready
    if storage:
        print(f"📦 Syncing storage '{LABEL_STUDIO_INIT_PROJECT}'...", end=" ")
        ls.import_storage.local.sync(
            id=storage.id
        )
        print(f"Storage '{LABEL_STUDIO_INIT_PROJECT}' synced successfully.")
        return storage.id


if __name__ == "__main__":
    args = parser.parse_args()

    # Define the label studio instance
    ls = LabelStudio(
        base_url=LABEL_STUDIO_URL,
        api_key=args.token,
    )

    # Load configs
    with open(CONFIG_PATH, "r") as f:
        configs = json.load(f)

    # Create the project
    project_id = create_project(ls, configs)

    # Create the localfile storage
    os.makedirs(LABEL_STUDIO_FILE_PATH, exist_ok=True)
    storage_id = create_storage(ls, project_id)

    # Save the startup data to a file
    with open("/label-studio/config/startup_data.json", "w") as f:
        json.dump({
            "token": args.token,
        }, f)
