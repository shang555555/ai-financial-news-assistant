import json
import logging

from openai import OpenAI

from src.config import Settings


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You summarize financial news for investors. "
    "Return valid JSON only with concise summaries."
)


class OpenAISummarizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if self.settings.use_deepseek:
            self.client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url="https://api.deepseek.com",
            )
        else:
            self.client = OpenAI(api_key=settings.openai_api_key)

    def summarize_batch(self, articles: list[dict], stock_symbol: str) -> tuple[dict[str, str], int]:
        summary_map: dict[str, str] = {}
        if not articles:
            return summary_map, 0

        api_calls = 0
        pending_batches = [articles[i : i + max(1, self.settings.summary_batch_size)] for i in range(0, len(articles), max(1, self.settings.summary_batch_size))]

        for batch in pending_batches:
            batch_summary_map, batch_calls = self._summarize_with_retry(batch, stock_symbol)
            summary_map.update(batch_summary_map)
            api_calls += batch_calls

        return summary_map, api_calls

    def _summarize_with_retry(self, batch: list[dict], stock_symbol: str) -> tuple[dict[str, str], int]:
        try:
            return self._summarize_single_batch(batch=batch, stock_symbol=stock_symbol), 1
        except Exception as exc:
            logger.warning("Batch summary failed, retrying in smaller batches: %s", exc)
            if len(batch) == 1:
                return self._fallback_map(batch), 1

            merged: dict[str, str] = {}
            api_calls = 0
            midpoint = max(1, len(batch) // 2)
            for sub_batch in (batch[:midpoint], batch[midpoint:]):
                if not sub_batch:
                    continue
                sub_summary_map, sub_calls = self._summarize_with_retry(sub_batch, stock_symbol)
                merged.update(sub_summary_map)
                api_calls += sub_calls
            return merged, api_calls

    def _summarize_single_batch(self, batch: list[dict], stock_symbol: str) -> dict[str, str]:
        user_prompt = self._build_user_prompt(batch=batch, stock_symbol=stock_symbol)
        response = self.client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )

        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("Empty summary response received from provider.")

        payload = self._extract_json(content)
        items = payload.get("summaries", [])
        summary_map = {}
        for item in items:
            title = (item.get("title") or "").strip()
            summary = (item.get("summary") or "").strip()
            if title:
                summary_map[title] = summary or "No summary generated."

        if not summary_map:
            raise ValueError("No valid summaries were returned.")

        fallback_map = self._fallback_map(batch)
        fallback_map.update(summary_map)
        return fallback_map

    @staticmethod
    def _build_user_prompt(batch: list[dict], stock_symbol: str) -> str:
        compact_articles = []
        for article in batch:
            compact_articles.append(
                {
                    "title": article["title"],
                    "content": article["content_text"][:500],
                }
            )

        return json.dumps(
            {
                "stock": stock_symbol,
                "rule": "For each article return one short summary under 24 words about event and market impact.",
                "format": {"summaries": [{"title": "same as input", "summary": "string"}]},
                "articles": compact_articles,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _extract_json(content: str) -> dict:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("No JSON object found in response.")
        return json.loads(content[start : end + 1])

    @staticmethod
    def _fallback_map(batch: list[dict]) -> dict[str, str]:
        fallback = {}
        for article in batch:
            text = article["content_text"].replace("\n", " ").strip()
            fallback[article["title"]] = text[:160] + ("..." if len(text) > 160 else "")
        return fallback
