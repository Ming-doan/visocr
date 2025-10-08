from typing import cast
import os
import argparse
import json
from label_studio_sdk.client import LabelStudio


# ---------------- Configuration ----------------

LABEL_STUDIO_URL = f"http://localhost:{os.getenv('LABEL_STUDIO_PORT', '8080')}"
CONFIG_PATH = "/label-studio/configs.json"
CACHE_PATH = "/label-studio/config/cache.json"

AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "http://localhost:9000")
AWS_S3_REGION = os.getenv("AWS_S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

# ------------------------------------------------


parser = argparse.ArgumentParser(description="Initialize Label Studio projects from configs.json")
parser.add_argument(
    "-t", "--token", type=str,
    help="API token for Label Studio. Go to `{host}/user/account` to get your token. Required at the first time.",
    default=None
)


def create_project(ls: LabelStudio, title: str, label_config_path: str) -> int:
    """Create a Label Studio project if not exists."""
    existing_projects = ls.projects.list()
    existing_titles = [project.title for project in existing_projects]

    if title in existing_titles:
        print(f"📦 Project '{title}' already exists. Skipping creation.")
        project = next(p for p in existing_projects if p.title == title)
        return project.id

    if not os.path.exists(label_config_path):
        raise FileNotFoundError(f"Label config not found: {label_config_path}")

    with open(label_config_path, "r", encoding="utf-8") as f:
        label_config = f.read()

    print(f"📦 Creating project '{title}'...")
    project = ls.projects.create(
        title=title,
        label_config=label_config,
        description=f"Auto-created project for {title}"
    )
    print(f"✅ Project '{title}' created successfully.")
    return project.id


def create_s3_storage(ls: LabelStudio, project_id: int, bucket: str, title: str):
    """Create MinIO (S3-compatible) import storage for the given project."""
    existing_storages = ls.import_storage.s3.list(project=project_id)
    existing_titles = [s.title for s in existing_storages]

    if title in existing_titles:
        print(f"🪣 Storage '{title}' already exists. Skipping creation.")
        storage = next(s for s in existing_storages if s.title == title)
        return storage.id

    print(f"🪣 Creating S3 import storage '{title}' for bucket '{bucket}'...")

    storage = ls.import_storage.s3.create(
        # S3 credentials
        s3endpoint=AWS_S3_ENDPOINT_URL,
        region_name=AWS_S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        # Project and bucket info
        project=project_id,
        title=title,
        prefix="",
        bucket=bucket,
        regex_filter=r".*\.(jpg|jpeg|png|gif|webp|jfif)$",
        # Other options
        use_blob_urls=True,
        recursive_scan=True,
        presign=False,
        presign_ttl=60,
    )

    print(f"✅ S3 storage '{title}' created successfully (id={storage.id}).")
    return storage.id




def main():
    args = parser.parse_args()

    # If token not provided, try to load from cache
    if args.token is None:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
                args.token = cache.get("token")
                print("🔑 Loaded token from cache.json")
        else:
            raise ValueError("API token is required at the first time. Provide it via --token")

    # Initialize Label Studio client
    ls = LabelStudio(base_url=LABEL_STUDIO_URL, api_key=args.token)

    # Load configs.json
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        configs = json.load(f)

    startup_data = {
        "token": args.token,
        "projects": [],
    }

    for model in configs.get("models", []):
        title = model["title"]
        label_config_path = f"/label-studio/config/{model['label_config']}"
        bucket = model["data_folder"].lower()

        print(f"\n🚀 Initializing: {title}")
        project_id = create_project(ls, title, label_config_path)
        storage_id = create_s3_storage(ls, project_id, bucket, title)

        startup_data["projects"].append({
            "title": title,
            "project_id": project_id,
            "storage_id": storage_id,
            "bucket": bucket,
        })

    # Save startup data
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(startup_data, f, indent=2)

    print("\n✅ All projects initialized successfully!")


if __name__ == "__main__":
    main()
