from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.ui_helpers import (
    escape,
    format_market_cap,
    format_price,
    sentiment_badge_class,
    sentiment_progress,
)


def render_hero() -> None:
    st.markdown(
        """
        <div class="glass-card hero-card">
          <div class="hero-row">
            <div>
              <div class="eyebrow">Good morning · AI Market Desk</div>
              <div class="hero-title">AI 金融新闻智能分析助手</div>
              <div class="hero-copy">
                像移动银行一样查看市场：输入任意美股代码，自动识别公司、抓取新闻、
                生成 DeepSeek 摘要，并把情绪信号整理成清晰的投资快照。
              </div>
            </div>
            <div class="avatar">AI</div>
          </div>
          <div class="mini-grid">
            <div class="metric-card">
              <div class="metric-value">Live</div>
              <div class="metric-label">今日市场情绪</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">99%</div>
              <div class="metric-label">分析成功率</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">AI</div>
              <div class="metric-label">智能总结引擎</div>
            </div>
            <div class="metric-card">
              <div class="metric-value">7D</div>
              <div class="metric-label">新闻覆盖窗口</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<div class="section-subtitle">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div>
          <div class="section-title">{escape(title)}</div>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_company_card(stock_symbol: str, company_name: str, stock_info: dict) -> None:
    price = (
        stock_info.get("currentPrice")
        or stock_info.get("regularMarketPrice")
        or stock_info.get("previousClose")
    )
    logo = escape((company_name or stock_symbol or "?")[:1].upper())
    sector = stock_info.get("sector") or "N/A"
    market_cap = format_market_cap(stock_info.get("marketCap"))
    st.markdown(
        f"""
        <div class="wallet-card">
          <div class="wallet-row">
            <div class="wallet-row" style="justify-content:flex-start;">
              <div class="company-logo">{logo}</div>
              <div>
                <div class="pill">{escape(stock_symbol)}</div>
                <div class="company-name">{escape(company_name or stock_symbol)}</div>
              </div>
            </div>
            <div style="text-align:right;">
              <div class="metric-value">{escape(format_price(price))}</div>
              <div class="metric-label">当前价格</div>
            </div>
          </div>
          <div class="mini-grid">
            <div class="metric-card">
              <div class="metric-value" style="font-size:24px;">{escape(sector)}</div>
              <div class="metric-label">行业</div>
            </div>
            <div class="metric-card">
              <div class="metric-value" style="font-size:28px;">{escape(market_cap)}</div>
              <div class="metric-label">市值</div>
            </div>
            <div class="metric-card">
              <div class="metric-value" style="font-size:28px;">{escape(stock_info.get("currency") or "USD")}</div>
              <div class="metric-label">报价货币</div>
            </div>
            <div class="metric-card">
              <div class="metric-value" style="font-size:28px;">{escape(stock_info.get("exchange") or "US")}</div>
              <div class="metric-label">交易市场</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_cards(df: pd.DataFrame, run_stats: dict[str, Any]) -> None:
    bullish = int((df["sentiment_label"] == "bullish").sum())
    bearish = int((df["sentiment_label"] == "bearish").sum())
    avg_score = float(df["sentiment_score"].mean())
    duration = float(run_stats.get("total_duration_seconds", 0))
    st.markdown(
        f"""
        <div class="mini-grid">
          <div class="metric-card">
            <div class="metric-value">{bullish}</div>
            <div class="metric-label">Bullish 新闻</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{bearish}</div>
            <div class="metric-label">Bearish 新闻</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{avg_score:.2f}</div>
            <div class="metric-label">平均情绪分</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{duration:.1f}s</div>
            <div class="metric-label">AI 分析耗时</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_news_card(row: pd.Series) -> None:
    label = str(row.get("sentiment_label", "neutral"))
    score = row.get("sentiment_score", 0)
    progress = sentiment_progress(score)
    badge_class = sentiment_badge_class(label)
    published_at = row.get("published_at", "")
    published_text = "" if pd.isna(published_at) else str(published_at)
    st.markdown(
        f"""
        <div class="news-card">
          <div class="news-meta">
            <div class="source-tag">{escape(row.get("source", "Unknown"))} · {escape(published_text)}</div>
            <div class="sentiment-badge {badge_class}">{escape(label)}</div>
          </div>
          <div class="news-title">{escape(row.get("title", ""))}</div>
          <div class="news-summary">{escape(row.get("summary", ""))}</div>
          <div style="height:18px;"></div>
          <div class="card-row">
            <div style="flex:1;">
              <div class="progress-shell">
                <div class="progress-fill" style="width:{progress}%;"></div>
              </div>
              <div class="metric-label">情绪得分 {float(score):.3f}</div>
            </div>
            <a class="news-link" href="{escape(row.get("url", "#"))}" target="_blank">查看原文</a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_initial_state() -> None:
    st.markdown(
        """
        <div class="glass-card">
          <div class="section-title" style="margin-top:0;">准备开始</div>
          <div class="quiet">
            输入 API Key 和股票代码后，点击“开始 AI 分析”。结果会以移动金融产品的方式展示：
            公司资产卡、情绪概览、现代图表和新闻卡片流。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
