from prefect import flow

from providers.config import get_default_configs, FlowConfig


FLOW_NAME = "extract_layout_to_images"


@flow(name=FLOW_NAME)
def extract_layout_to_images_flow(configs: FlowConfig | None = None) -> None:
    configs = configs or get_default_configs(FLOW_NAME)