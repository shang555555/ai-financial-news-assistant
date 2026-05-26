import logging
import time
from dataclasses import replace

import streamlit as st

from src.analysis_service import NewsAnalysisService
from src.components import (
    render_company_card,
    render_hero,
    render_initial_state,
    render_news_card,
    render_overview_cards,
    render_section,
)
from src.config import Settings
from src.news_service import NewsService
from src.ui_helpers import (
    build_results_dataframe,
    get_company_name,
    get_secret,
    get_stock_info,
    load_css,
    make_sentiment_distribution_chart,
    make_sentiment_score_chart,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="AI Financial News Assistant",
    page_icon=":bar_chart:",
    layout="wide",
)


def render_input_panel(settings: Settings) -> tuple[Settings, str, str, str, int, bool, str, dict]:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section("Secure Market Access", "API Key 只在当前会话中使用，刷新页面后不会持久化保存。")

    key_col1, key_col2 = st.columns(2)
    with key_col1:
        user_news_api_key = st.text_input(
            "NewsAPI Key",
            type="password",
            placeholder="Paste your NewsAPI key",
        )
        st.markdown("[Get NewsAPI Key](https://newsapi.org)")
    with key_col2:
        user_deepseek_api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            placeholder="Paste your DeepSeek key",
        )
        st.markdown("[Get DeepSeek API Key](https://platform.deepseek.com)")

    news_api_key = user_news_api_key or get_secret("NEWS_API_KEY", "")
    deepseek_api_key = user_deepseek_api_key or get_secret("DEEPSEEK_API_KEY", "")
    settings = replace(
        settings,
        news_api_key=news_api_key,
        deepseek_api_key=deepseek_api_key,
    )

    input_col, slider_col = st.columns([2, 1])
    with input_col:
        stock_symbol = st.text_input(
            "股票代码",
            value="AAPL",
            placeholder="输入股票代码，例如 NVDA / TSLA / AAPL",
        ).strip().upper()
    with slider_col:
        max_articles = st.slider("新闻数量", min_value=3, max_value=10, value=5)

    run_button = st.button("开始 AI 分析", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    stock_info = get_stock_info(stock_symbol) if stock_symbol else {}
    company_name = get_company_name(stock_symbol, stock_info)
    return (
        settings,
        news_api_key,
        deepseek_api_key,
        stock_symbol,
        max_articles,
        run_button,
        company_name,
        stock_info,
    )


def run_analysis(
    settings: Settings,
    news_api_key: str,
    deepseek_api_key: str,
    stock_symbol: str,
    company_name: str,
    max_articles: int,
) -> tuple[list[dict], dict] | None:
    news_service = NewsService(settings=settings, news_api_key=news_api_key)
    analysis_service = NewsAnalysisService(
        settings=settings,
        deepseek_api_key=deepseek_api_key,
    )

    with st.spinner("正在连接市场新闻源与 DeepSeek 分析引擎..."):
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
            return None

        if not articles:
            st.warning("没有查询到相关新闻。你可以换一个股票代码，或稍后再试。")
            return None

        try:
            analyzed_records, run_stats = analysis_service.analyze_articles(
                stock_symbol=stock_symbol,
                articles=articles,
            )
            run_stats["total_duration_seconds"] = time.perf_counter() - run_started_at
        except Exception as exc:
            logger.exception("Failed to analyze news")
            st.error(f"新闻分析失败: {exc}")
            return None

    return analyzed_records, run_stats


def main() -> None:
    load_css()
    settings = Settings.from_env()

    st.markdown('<main class="app-shell">', unsafe_allow_html=True)
    render_hero()

    (
        settings,
        news_api_key,
        deepseek_api_key,
        stock_symbol,
        max_articles,
        run_button,
        company_name,
        stock_info,
    ) = render_input_panel(settings)

    if stock_symbol:
        if not stock_info or company_name == stock_symbol:
            st.warning("无法获取公司信息，已使用 ticker 作为搜索关键词。")
        render_company_card(stock_symbol, company_name, stock_info)

    if not news_api_key or not deepseek_api_key:
        st.warning("Please input your API keys.")
        st.markdown("</main>", unsafe_allow_html=True)
        st.stop()

    if not stock_symbol:
        st.warning("请输入有效的股票代码，例如 `AAPL` 或 `TSLA`。")
        st.markdown("</main>", unsafe_allow_html=True)
        st.stop()

    if not run_button:
        render_initial_state()
        st.markdown("</main>", unsafe_allow_html=True)
        return

    result = run_analysis(
        settings=settings,
        news_api_key=news_api_key,
        deepseek_api_key=deepseek_api_key,
        stock_symbol=stock_symbol,
        company_name=company_name,
        max_articles=max_articles,
    )
    if result is None:
        st.markdown("</main>", unsafe_allow_html=True)
        return

    analyzed_records, run_stats = result
    df = build_results_dataframe(analyzed_records)
    if df.empty:
        st.warning("分析结果为空。")
        st.markdown("</main>", unsafe_allow_html=True)
        return

    render_section("市场情绪概览", "AI 将新闻摘要、情绪分数与缓存表现整理成实时信号。")
    render_overview_cards(df, run_stats)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(make_sentiment_distribution_chart(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(make_sentiment_score_chart(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section("AI 新闻卡片", "每条新闻都被整理成来源、摘要、情绪标签和可操作链接。")
    for _, row in df.iterrows():
        render_news_card(row)

    render_section("数据导出", "保留原始分析结果，方便继续研究或归档。")
    st.dataframe(
        df[["title", "summary", "sentiment_label", "sentiment_score", "source", "published_at"]],
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        label="下载结果 CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{stock_symbol.lower()}_news_analysis.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("</main>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
