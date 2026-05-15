from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests

from src.config import Settings


logger = logging.getLogger(__name__)


TICKER_ALIASES = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "META": "Meta",
    "GOOGL": "Google",
    "AMD": "AMD",
}


class NewsService:
    base_url = "https://newsapi.org/v2/everything"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_news(self, stock_symbol: str, limit: int = 5) -> list[dict]:
        company_name = TICKER_ALIASES.get(stock_symbol.upper(), stock_symbol.upper())
        query = f'("{stock_symbol}" OR "{company_name}") AND (stock OR shares OR earnings OR market)'
        from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "language": self.settings.news_language,
            "sortBy": "publishedAt",
            "pageSize": min(limit, self.settings.news_page_size),
            "from": from_date,
        }
        headers = {"X-Api-Key": self.settings.news_api_key}

        logger.info("Fetching news | stock=%s limit=%s", stock_symbol, limit)
        response = requests.get(
            self.base_url,
            params=params,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()

        payload = response.json()
        articles = payload.get("articles", [])

        cleaned_articles = []
        seen_titles = set()

        for article in articles:
            title = (article.get("title") or "").strip()
            description = (article.get("description") or "").strip()
            content = (article.get("content") or "").strip()
            content_text = self._build_content_text(title, description, content)

            if not title or not content_text or title in seen_titles:
                continue

            seen_titles.add(title)
            cleaned_articles.append(
                {
                    "title": title,
                    "content_text": content_text,
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "published_at": article.get("publishedAt", ""),
                    "url": article.get("url", ""),
                }
            )

        logger.info("Fetched news done | raw=%s cleaned=%s", len(articles), len(cleaned_articles))
        return cleaned_articles[:limit]

    @staticmethod
    def _build_content_text(title: str, description: str, content: str) -> str:
        parts = []
        if title:
            parts.append(f"Title: {title}")
        if description:
            parts.append(f"Description: {description}")
        if content:
            parts.append(f"Content: {content}")
        return "\n".join(parts)
