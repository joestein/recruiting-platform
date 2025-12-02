from .graph_client_base import GraphClient
from .age_graph_client import AgeGraphClient
from .neptune_graph_client import NeptuneGraphClient


def get_graph_client(settings) -> GraphClient:
    """
    Return a graph client based on configuration.
    """
    backend = (settings.GRAPH_BACKEND or "age").lower()
    if backend == "age":
        return AgeGraphClient(
            host=settings.AGE_HOST,
            port=settings.AGE_PORT,
            database=settings.AGE_DB,
            user=settings.AGE_USER,
            password=settings.AGE_PASSWORD,
            graph_name=settings.AGE_GRAPH_NAME,
        )
    if backend == "neptune":
        return NeptuneGraphClient(
            endpoint=settings.NEPTUNE_ENDPOINT,
            port=settings.NEPTUNE_PORT,
            region=settings.NEPTUNE_REGION,
            use_https=settings.NEPTUNE_USE_HTTPS,
            use_bolt=settings.NEPTUNE_USE_BOLT,
        )
    raise ValueError(f"Unsupported GRAPH_BACKEND: {settings.GRAPH_BACKEND}")
