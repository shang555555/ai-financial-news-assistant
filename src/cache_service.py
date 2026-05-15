import hashlib
import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class NewsAnalysisCache:
    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if not self.cache_path.exists():
            return {"by_title": {}, "by_key": {}}

        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Cache file is invalid JSON, starting with an empty cache.")
            return {"by_title": {}, "by_key": {}}
        except OSError as exc:
            logger.warning("Failed to read cache file: %s", exc)
            return {"by_title": {}, "by_key": {}}

        if "by_title" not in data and "by_key" not in data:
            legacy_title_map = data if isinstance(data, dict) else {}
            return {
                "by_title": legacy_title_map,
                "by_key": {},
            }

        data.setdefault("by_title", {})
        data.setdefault("by_key", {})
        return data

    def get(self, article: dict) -> dict | None:
        title = self._normalize_title(article["title"])
        cache_key = self._build_cache_key(article)
        by_key = self._data.get("by_key", {})
        by_title = self._data.get("by_title", {})
        return by_key.get(cache_key) or by_title.get(title)

    def set(self, article: dict, record: dict) -> None:
        title = self._normalize_title(article["title"])
        cache_key = self._build_cache_key(article)
        self._data.setdefault("by_title", {})[title] = record
        self._data.setdefault("by_key", {})[cache_key] = record

    def size(self) -> int:
        return len(self._data.get("by_key", {})) or len(self._data.get("by_title", {}))

    def save(self) -> None:
        try:
            self.cache_path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Failed to write cache file: %s", exc)

    @staticmethod
    def _normalize_title(title: str) -> str:
        return " ".join((title or "").strip().lower().split())

    @classmethod
    def _build_cache_key(cls, article: dict) -> str:
        normalized_title = cls._normalize_title(article.get("title", ""))
        source = (article.get("source") or "").strip().lower()
        published_at = (article.get("published_at") or "").strip().lower()
        key_raw = f"{normalized_title}|{source}|{published_at}"
        return hashlib.sha256(key_raw.encode("utf-8")).hexdigest()
