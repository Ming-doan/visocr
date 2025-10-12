from typing import Any
import os
import json
from functools import lru_cache

from label_studio_sdk.client import LabelStudio


APP_HOST = os.getenv("APP_HOST", "localhost")
LABEL_STUDIO_HOST = os.getenv("LABEL_STUDIO_HOST", APP_HOST)
LABEL_STUDIO_CACHE_PATH = os.getenv(
    "LABEL_STUDIO_CACHE_PATH",
    os.path.join(os.getcwd(), "label-studio-data", "cache.json")
)


@lru_cache(maxsize=1)
def get_label_studio_data() -> dict[str, Any]:
    # Try to load cache file if exists
    if os.path.exists(LABEL_STUDIO_CACHE_PATH):
        with open(LABEL_STUDIO_CACHE_PATH, "r", encoding="utf-8") as f:
            cache_data: dict[str, Any] = json.load(f)
    else:
        raise FileNotFoundError(f"Label Studio cache file not found at {LABEL_STUDIO_CACHE_PATH}")
    return cache_data


@lru_cache(maxsize=1)
def get_label_studio_client():
    cache_data = get_label_studio_data()
    return LabelStudio(
        url=f"http://{LABEL_STUDIO_HOST}:8080",
        api_key=os.getenv("LABEL_STUDIO_API_KEY", cache_data.get("token")),
    )

