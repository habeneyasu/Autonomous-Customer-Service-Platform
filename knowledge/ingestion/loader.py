from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_SOURCES_DIR = Path(__file__).resolve().parents[1] / "sources"


@dataclass(frozen=True)
class LoadedDocument:
    document_id: str
    title: str
    content: str
    source: str
    topic: str
    tags: tuple[str, ...]
    file_name: str
    file_path: str
    last_updated: datetime


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw

    metadata: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, parts[2].lstrip("\n")


def _extract_title(content: str, file_name: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return file_name.removesuffix(".md").replace("-", " ").title()


def _parse_tags(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(tag.strip() for tag in raw.split(",") if tag.strip())


def load_markdown_file(path: Path) -> LoadedDocument:
    raw = path.read_text(encoding="utf-8")
    metadata, content = _parse_frontmatter(raw)
    title = _extract_title(content, path.name)
    source = metadata.get("source", f"policy/{path.stem}")
    topic = source.split("/")[-1].replace("-", " ")

    return LoadedDocument(
        document_id=metadata.get("document_id", path.stem),
        title=title,
        content=content,
        source=source,
        topic=topic,
        tags=_parse_tags(metadata.get("tags")),
        file_name=path.name,
        file_path=str(path.resolve()),
        last_updated=datetime.fromtimestamp(path.stat().st_mtime),
    )


def load_markdown_sources(sources_dir: Path | None = None) -> list[LoadedDocument]:
    directory = sources_dir or DEFAULT_SOURCES_DIR
    if not directory.exists():
        raise FileNotFoundError(f"Knowledge sources directory not found: {directory}")

    return [load_markdown_file(path) for path in sorted(directory.glob("*.md"))]
