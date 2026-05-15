import logging

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer


logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self) -> None:
        try:
            nltk.download("vader_lexicon", quiet=True)
        except Exception as exc:
            logger.warning("Failed to download vader_lexicon: %s", exc)
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text: str) -> dict:
        scores = self.analyzer.polarity_scores(text or "")
        compound = scores["compound"]

        if compound >= 0.2:
            label = "bullish"
        elif compound <= -0.2:
            label = "bearish"
        else:
            label = "neutral"

        return {
            "label": label,
            "compound": compound,
            "detail": scores,
        }
