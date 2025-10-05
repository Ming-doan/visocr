from functools import lru_cache
from label_studio_sdk.client import LabelStudio


@lru_cache(maxsize=1)
def get_label_studio_client():
    return LabelStudio(
        url="http://localhost:8080",
        api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6ODA2NTgxOTg5MywiaWF0IjoxNzU4NjE5ODkzLCJqdGkiOiJkZjcwYjJmOTk2MGU0MDY1YmMzOGQ3NmEyODg5YzE2NCIsInVzZXJfaWQiOjF9.brWG80dlfxXhRAZMzYLfIz1vMKFb2b4j_glZSnI5HNE"
    )