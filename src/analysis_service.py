import logging
import time

from src.cache_service import NewsAnalysisCache
from src.config import Settings
from src.sentiment import SentimentAnalyzer
from src.summarizer import OpenAISummarizer


logger = logging.getLogger(__name__)


class NewsAnalysisService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache = NewsAnalysisCache(settings.cache_file_path)
        self.summarizer = OpenAISummarizer(settings)
        self.sentiment_analyzer = SentimentAnalyzer()

    def analyze_articles(self, stock_symbol: str, articles: list[dict]) -> tuple[list[dict], dict]:
        results: list[dict] = []
        new_articles: list[dict] = []
        cache_hits = 0

        for article in articles:
            cached_record = self.cache.get(article)
            if cached_record:
                results.append(cached_record)
                cache_hits += 1
                continue
            new_articles.append(article)

        logger.info(
            "News analysis started | stock=%s total=%s cache_hits=%s new=%s",
            stock_symbol,
            len(articles),
            cache_hits,
            len(new_articles),
        )

        api_duration_seconds = 0.0
        api_calls = 0

        if new_articles:
            start_time = time.perf_counter()
            summary_map, api_calls = self.summarizer.summarize_batch(
                articles=new_articles,
                stock_symbol=stock_symbol,
            )
            api_duration_seconds = time.perf_counter() - start_time

            for article in new_articles:
                sentiment = self.sentiment_analyzer.analyze(article["content_text"])
                analyzed_record = {
                    "stock_symbol": stock_symbol,
                    "title": article["title"],
                    "summary": summary_map.get(article["title"], "No summary generated."),
                    "sentiment_label": sentiment["label"],
                    "sentiment_score": sentiment["compound"],
                    "source": article["source"],
                    "published_at": article["published_at"],
                    "url": article["url"],
                    "raw_content": article["content_text"],
                }
                results.append(analyzed_record)
                self.cache.set(article, analyzed_record)

            self.cache.save()

        ordered_results = self._sort_like_source(articles, results)
        total_articles = max(1, len(articles))
        run_stats = {
            "cache_hits": cache_hits,
            "new_articles": len(new_articles),
            "api_calls": api_calls,
            "api_duration_seconds": api_duration_seconds,
            "cache_hit_rate": cache_hits / total_articles,
            "cache_size": self.cache.size(),
        }
        logger.info("News analysis finished | stats=%s", run_stats)
        return ordered_results, run_stats

    @staticmethod
    def _sort_like_source(source_articles: list[dict], analyzed_records: list[dict]) -> list[dict]:
        record_map = {record["title"]: record for record in analyzed_records}
        ordered = []
        for article in source_articles:
            record = record_map.get(article["title"])
            if record:
                ordered.append(record)
        return ordered
