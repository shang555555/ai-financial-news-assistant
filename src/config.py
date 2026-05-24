import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    openai_api_key: str
    openai_model: str
    deepseek_api_key: str
    deepseek_flash_model: str
    deepseek_pro_model: str
    deepseek_advanced_mode: bool
    news_api_key: str
    news_language: str
    news_page_size: int
    max_tokens: int
    temperature: float
    summary_batch_size: int
    cache_file_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        project_root = Path(__file__).resolve().parent.parent
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            deepseek_api_key="",
            deepseek_flash_model=os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash"),
            deepseek_pro_model=os.getenv("DEEPSEEK_PRO_MODEL", "deepseek-v4-pro"),
            deepseek_advanced_mode=_to_bool(os.getenv("DEEPSEEK_ADVANCED_MODE", "false")),
            news_api_key="",
            news_language=os.getenv("NEWS_LANGUAGE", "en"),
            news_page_size=int(os.getenv("NEWS_PAGE_SIZE", "10")),
            max_tokens=int(os.getenv("SUMMARY_MAX_TOKENS", "120")),
            temperature=float(os.getenv("SUMMARY_TEMPERATURE", "0.1")),
            summary_batch_size=int(os.getenv("SUMMARY_BATCH_SIZE", "5")),
            cache_file_path=project_root / "analyzed_news.json",
        )

    @property
    def use_deepseek(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def active_deepseek_model(self) -> str:
        return self.deepseek_pro_model if self.deepseek_advanced_mode else self.deepseek_flash_model

    @property
    def model(self) -> str:
        if self.use_deepseek:
            return self.active_deepseek_model
        return self.openai_model

    @property
    def api_provider(self) -> str:
        return "DeepSeek" if self.use_deepseek else "OpenAI"
