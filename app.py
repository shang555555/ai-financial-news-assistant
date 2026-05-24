import logging
import time
from dataclasses import replace

import pandas as pd
import streamlit as st
import yfinance as yf

from src.analysis_service import NewsAnalysisService
from src.config import Settings
from src.news_service import NewsService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="金融新闻智能分析助手",
    page_icon=":bar_chart:",
    layout="wide",
)


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


def format_price(price: object) -> str:
    if isinstance(price, (int, float)):
        return f"${price:,.2f}"
    return "N/A"


def format_market_cap(market_cap: object) -> str:
    if not isinstance(market_cap, (int, float)):
        return "N/A"

    if market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.2f}T"
    if market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.2f}B"
    if market_cap >= 1_000_000:
        return f"${market_cap / 1_000_000:.2f}M"
    return f"${market_cap:,.0f}"


def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def build_results_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    if "published_at" in df.columns:
        df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    return df


def main() -> None:
    st.title("金融新闻智能分析助手")
    st.caption("输入股票代码，自动抓取相关新闻，生成摘要，并给出情绪分类。")

    settings = Settings.from_env()

    with st.sidebar:
        st.header("API Keys")
        user_news_api_key = st.text_input("NewsAPI Key", type="password")
        user_deepseek_api_key = st.text_input("DeepSeek API Key", type="password")
        st.markdown("[Get NewsAPI Key](https://newsapi.org)")
        st.markdown("[Get DeepSeek API Key](https://platform.deepseek.com)")

        news_api_key = user_news_api_key or get_secret("NEWS_API_KEY", "")
        deepseek_api_key = user_deepseek_api_key or get_secret("DEEPSEEK_API_KEY", "")
        settings = replace(
            settings,
            news_api_key=news_api_key,
            deepseek_api_key=deepseek_api_key,
        )

        st.header("参数配置")
        stock_symbol = st.text_input("股票代码", value="AAPL").strip().upper()
        max_articles = st.slider("分析新闻数量", min_value=3, max_value=10, value=5)
        run_button = st.button("开始分析", type="primary", use_container_width=True)

        stock_info = get_stock_info(stock_symbol) if stock_symbol else {}
        company_name = get_company_name(stock_symbol, stock_info)
        has_company_info = bool(stock_info) and company_name != stock_symbol

        st.markdown("### 公司信息")
        if stock_symbol and not has_company_info:
            st.warning("无法获取公司信息，已使用 ticker 作为搜索关键词。")
        st.write(f"公司名称: `{company_name or 'N/A'}`")
        st.metric(
            "当前价格",
            format_price(
                stock_info.get("currentPrice")
                or stock_info.get("regularMarketPrice")
                or stock_info.get("previousClose")
            ),
        )
        st.write(f"行业: `{stock_info.get('sector') or 'N/A'}`")
        st.write(f"市值: `{format_market_cap(stock_info.get('marketCap'))}`")

        st.markdown("### 当前配置")
        st.write(f"新闻语言: `{settings.news_language}`")
        st.write(f"摘要提供方: `{settings.api_provider}`")
        st.write(f"摘要模型: `{settings.model}`")
        st.write(f"批处理大小: `{settings.summary_batch_size}`")
        st.write(f"缓存文件: `{settings.cache_file_path.name}`")

    if not news_api_key or not deepseek_api_key:
        st.warning("Please input your API keys.")
        st.stop()

    if not run_button:
        st.info("在左侧输入股票代码后，点击“开始分析”。")
        return

    if not stock_symbol:
        st.warning("请输入有效的股票代码，例如 `AAPL` 或 `TSLA`。")
        return

    news_service = NewsService(settings=settings, news_api_key=news_api_key)
    analysis_service = NewsAnalysisService(
        settings=settings,
        deepseek_api_key=deepseek_api_key,
    )

    with st.spinner("正在获取新闻并进行分析，请稍候..."):
        run_started_at = time.perf_counter()
        try:
            articles = news_service.fetch_news(
                stock_symbol=stock_symbol,
                company_name=company_name,
                limit=max_articles,
            )
        except Exception as exc:
            logger.exception("Failed to fetch news")
            st.error(f"新闻获取失败: {exc}")
            return

        if not articles:
            st.warning("没有查询到相关新闻。你可以换一个股票代码，或稍后再试。")
            return

        try:
            analyzed_records, run_stats = analysis_service.analyze_articles(
                stock_symbol=stock_symbol,
                articles=articles,
            )
            run_stats["total_duration_seconds"] = time.perf_counter() - run_started_at
        except Exception as exc:
            logger.exception("Failed to analyze news")
            st.error(f"新闻分析失败: {exc}")
            return

    df = build_results_dataframe(analyzed_records)

    if df.empty:
        st.warning("分析结果为空。")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("新闻数量", len(df))
    col2.metric("平均情绪分数", f"{df['sentiment_score'].mean():.2f}")
    col3.metric("最常见情绪", df["sentiment_label"].mode().iloc[0])

    perf1, perf2, perf3, perf4 = st.columns(4)
    perf1.metric("缓存命中", run_stats["cache_hits"])
    perf2.metric("新增分析", run_stats["new_articles"])
    perf3.metric("API 调用次数", run_stats["api_calls"])
    perf4.metric("命中率", f"{run_stats['cache_hit_rate']:.0%}")

    perf5, perf6, perf7 = st.columns(3)
    perf5.metric("API 耗时", f"{run_stats['api_duration_seconds']:.2f}s")
    perf6.metric("页面总耗时", f"{run_stats['total_duration_seconds']:.2f}s")
    perf7.metric("缓存记录数", run_stats["cache_size"])

    st.subheader("情绪分布")
    sentiment_counts = (
        df["sentiment_label"]
        .value_counts()
        .reindex(["bullish", "neutral", "bearish"], fill_value=0)
    )
    st.bar_chart(sentiment_counts)

    st.subheader("情绪分数")
    chart_df = df[["title", "sentiment_score"]].copy()
    chart_df = chart_df.set_index("title")
    st.bar_chart(chart_df)

    st.subheader("新闻详情")
    for _, row in df.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['title']}")
            st.write(f"来源: `{row['source']}`")
            if pd.notna(row["published_at"]):
                st.write(f"发布时间: `{row['published_at']}`")
            st.write(f"情绪分类: `{row['sentiment_label']}`")
            st.write(f"情绪得分: `{row['sentiment_score']:.3f}`")
            st.markdown("**摘要**")
            st.write(row["summary"])
            st.markdown("**正文片段**")
            st.write(row["raw_content"])
            st.markdown(f"[查看原文]({row['url']})")

    st.subheader("结果表格")
    st.dataframe(
        df[["title", "summary", "sentiment_label", "sentiment_score", "source", "published_at"]],
        use_container_width=True,
    )

    st.download_button(
        label="下载结果 CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{stock_symbol.lower()}_news_analysis.csv",
        mime="text/csv",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
