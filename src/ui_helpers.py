from __future__ import annotations

import html
import logging
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
    ticker = ticker.strip().upper()
    if not ticker:
        return {}

    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        logger.exception("Failed to fetch stock info | ticker=%s", ticker)
        return {}


def get_company_name(ticker: str, stock_info: dict) -> str:
    return stock_info.get("shortName") or stock_info.get("longName") or ticker


def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def format_price(price: Any) -> str:
    if isinstance(price, (int, float)):
        return f"${price:,.2f}"
    return "N/A"


def format_market_cap(market_cap: Any) -> str:
    if not isinstance(market_cap, (int, float)):
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
