from pathlib import Path

from shared.config.settings import get_settings

_settings = get_settings()
KNOWLEDGE_INDEX_DIR = Path(_settings.knowledge_index_dir)
COLLECTION_NAME = "acsp_knowledge"


def get_index_path() -> Path:
    path = KNOWLEDGE_INDEX_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path
