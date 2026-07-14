"""插件市场存储层。

负责市场索引（index.json）和包文件（packages/*.zip）的读写。
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def load_index(marketplace_index: Path) -> list[dict]:
    """读取市场索引，不存在则返回空列表。"""
    if not marketplace_index.exists():
        return []
    try:
        data = json.loads(marketplace_index.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_index(marketplace_dir: Path, items: list[dict]) -> None:
    """保存市场索引。"""
    marketplace_dir.mkdir(parents=True, exist_ok=True)
    index_path = marketplace_dir / "index.json"
    index_path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def now_iso() -> str:
    """当前 UTC 时间 ISO 字符串。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
