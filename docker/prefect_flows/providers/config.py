from typing import Any
import os
import json
from functools import lru_cache

CONFIG_PATH = os.getenv("CONFIG_PATH", os.path.join(os.getcwd(), "docker", "configs.json"))


FlowConfig = dict[str, Any]


@lru_cache(maxsize=1)
def get_default_configs(flow_name: str | None) -> FlowConfig:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    flow_conf: dict[str, FlowConfig] = data.get("flow", {})
    if flow_name:
        return flow_conf[flow_name]
    return {}