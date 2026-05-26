from __future__ import annotations

import html
import logging
from numbers import Real
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


logger = logging.getLogger(__name__)


def load_css(path: str = "styles.css") -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_stock_info(ticker: str) -> dict:
    symbol = ticker.strip().upper()
    company_info = {
        "name": symbol,
        "symbol": symbol,
        "price": None,
        "industry": "Unknown",
        "market_cap": None,
        "currency": None,
    }
    if not symbol:
        print("Company info:", company_info)
        return company_info

    try:
        stock = yf.Ticker(symbol)

        fast_info = {}
        try:
            fast_info = stock.fast_info or {}
        except Exception:
            logger.exception("Failed to fetch fast_info | ticker=%s", symbol)

        company_info["price"] = _fast_info_value(fast_info, "lastPrice")
        company_info["market_cap"] = _fast_info_value(fast_info, "marketCap")
        company_info["currency"] = _fast_info_value(fast_info, "currency")

        info = {}
        try:
            info = stock.info or {}
        except Exception:
            logger.exception("Failed to fetch info | ticker=%s", symbol)

        company_info["name"] = info.get("shortName") or symbol
        company_info["industry"] = info.get("industry") or "Unknown"

        if company_info["price"] is None:
            company_info["price"] = _latest_close_price(stock, symbol)
    except Exception:
        logger.exception("Failed to fetch company info | ticker=%s", symbol)

    print("Company info:", company_info)
    return company_info


def get_company_name(ticker: str, stock_info: dict) -> str:
    return stock_info.get("name") or ticker


def _fast_info_value(fast_info: Any, key: str) -> Any:
    try:
        value = fast_info[key]
    except Exception:
        try:
            value = getattr(fast_info, key)
        except Exception:
            return None

    if value is None:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except Exception:
        pass
    return value


def _latest_close_price(stock: yf.Ticker, symbol: str) -> float | None:
    try:
        history = stock.history(period="1d")
    except Exception:
        logger.exception("Failed to fetch price history | ticker=%s", symbol)
        return None

    if history.empty or "Close" not in history.columns:
        return None

    close_price = history["Close"].dropna()
    if close_price.empty:
        return None
    return float(close_price.iloc[-1])


def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def format_price(price: Any) -> str:
    if isinstance(price, Real) and not isinstance(price, bool):
        return f"${price:,.2f}"
    return "N/A"


def format_market_cap(market_cap: Any) -> str:
    if not isinstance(market_cap, Real) or isinstance(market_cap, bool):
        return "N/A"

    if market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.2f}T"
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    if market_cap >= 1_000_000:
        return f"${market_cap / 1_000_000:.2f}M"
    return f"${market_cap:,.0f}"


def escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def build_results_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    return df


def sentiment_progress(score: Any) -> int:
    try:
        value = float(score)
    except (TypeError, ValueError):
        return 50
    return max(0, min(100, round((value + 1) * 50)))


def sentiment_badge_class(label: str) -> str:
    label = (label or "neutral").lower()
    if label == "bullish":
        return "sentiment-bullish"
    if label == "bearish":
        return "sentiment-bearish"
    return "sentiment-neutral"


def chart_layout(title: str) -> dict:
    return {
        "title": {"text": title, "font": {"size": 22, "color": "#f8fafc"}},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter", "color": "rgba(226,232,240,0.86)"},
        "margin": {"l": 20, "r": 20, "t": 64, "b": 34},
        "height": 360,
        "xaxis": {
            "gridcolor": "rgba(148,163,184,0.12)",
            "zerolinecolor": "rgba(148,163,184,0.12)",
        },
        "yaxis": {
            "gridcolor": "rgba(148,163,184,0.12)",
            "zerolinecolor": "rgba(148,163,184,0.12)",
        },
        "showlegend": False,
    }


def make_sentiment_distribution_chart(df: pd.DataFrame) -> go.Figure:
    counts = (
        df["sentiment_label"]
        .value_counts()
        .reindex(["bullish", "neutral", "bearish"], fill_value=0)
    )
    colors = ["#34d399", "#38bdf8", "#fb7185"]
    fig = go.Figure(
        data=[
            go.Bar(
                x=counts.index,
                y=counts.values,
                marker={
                    "color": colors,
                    "line": {"color": "rgba(255,255,255,0.24)", "width": 1},
                },
                text=counts.values,
                textposition="outside",
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        ]
    )
    fig.update_layout(**chart_layout("市场情绪分布"))
    return fig


def make_sentiment_score_chart(df: pd.DataFrame) -> go.Figure:
    chart_df = df[["title", "sentiment_score"]].copy()
    chart_df["short_title"] = chart_df["title"].str.slice(0, 34)
    fig = go.Figure(
        data=[
            go.Bar(
                x=chart_df["sentiment_score"],
                y=chart_df["short_title"],
                orientation="h",
                marker={
                    "color": chart_df["sentiment_score"],
                    "colorscale": [[0, "#fb7185"], [0.5, "#38bdf8"], [1, "#34d399"]],
                    "cmin": -1,
                    "cmax": 1,
                },
                hovertemplate="%{y}<br>Score: %{x:.3f}<extra></extra>",
            )
        ]
    )
    fig.update_layout(**chart_layout("新闻情绪强度"))
    fig.update_xaxes(range=[-1, 1])
    return fig
