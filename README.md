# Financial News Intelligence Assistant

基于 Python、Streamlit、NewsAPI 和大模型 API 的金融新闻智能分析项目。

用户输入股票代码后，系统会自动抓取相关新闻，生成摘要，完成情绪分类，并以可视化方式展示分析结果。项目重点优化了缓存复用、增量分析和批量摘要，适合放在 GitHub 作为工程化作品，也适合继续扩展成量化研究或投研辅助工具。

## Highlights

- 输入股票代码后自动抓取相关新闻
- 使用 DeepSeek 或 OpenAI 生成投资者视角摘要
- 使用 VADER 对新闻做 `bullish / bearish / neutral` 情绪分类
- 使用 Streamlit 展示指标、图表、新闻详情和结果表格
- 本地 JSON 缓存避免重复分析
- 增量更新，只分析新增新闻
- 批量摘要减少 API 调用次数
- 展示缓存命中率、API 调用次数、API 耗时、总耗时
- 支持导出分析结果 CSV

## Why This Project

这个项目的目标不是做一个复杂的大而全平台，而是做一个可以快速交付、容易部署、便于展示工程思路的 MVP：

- 对简历友好：从数据获取、模型调用、情绪分析到前端展示形成完整闭环
- 对成本友好：通过缓存、批处理和更短 prompt 显著减少 token 消耗
- 对扩展友好：后续可以接数据库、消息推送、行情联动、回测系统

## Demo Features

1. 输入股票代码，例如 `AAPL`、`TSLA`、`NVDA`
2. 获取近 7 天相关新闻
3. 对新增新闻批量生成摘要
4. 对每条新闻进行情绪分析
5. 展示：
   - 新闻标题
   - 新闻摘要
   - 情绪分类
   - 情绪分数
   - 情绪分布图
   - CSV 下载

## Tech Stack

- Python 3.10+
- Streamlit
- pandas
- requests
- openai
- nltk / VADER
- NewsAPI

## Project Structure

```text
financial-news-intelligence-assistant/
├── analyzed_news.json
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── DEPLOYMENT.md
├── .streamlit/
│   └── secrets.toml.example
└── src/
    ├── __init__.py
    ├── analysis_service.py
    ├── cache_service.py
    ├── config.py
    ├── news_service.py
    ├── sentiment.py
    └── summarizer.py
```

## Architecture

```text
User Input -> NewsAPI -> News Cleaning -> Cache Check
                                   |-> Cached -> UI
                                   |-> New Items -> Batch Summarizer -> Sentiment Analyzer -> Cache Save -> UI
```

## Cost Optimization Design

- 缓存文件 `analyzed_news.json` 保存已分析结果
- 相同新闻优先走缓存，不重复调用模型
- 批量摘要减少逐条请求带来的开销
- 固定 `system prompt`，尽量提高 provider 侧 cache hit
- 默认使用 `deepseek-v4-flash`
- 仅在高级模式下切换到 `deepseek-v4-pro`
- `max_tokens=120`
- `temperature=0.1`

## Quick Start

### 1. Clone repository

```bash
git clone <your-repo-url>
cd financial-news-intelligence-assistant
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

复制 `.env.example` 为 `.env`，填入自己的 API Key：

```env
NEWS_API_KEY=your_newsapi_key
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=

DEEPSEEK_FLASH_MODEL=deepseek-v4-flash
DEEPSEEK_PRO_MODEL=deepseek-v4-pro
DEEPSEEK_ADVANCED_MODE=false

OPENAI_MODEL=gpt-4.1-mini
NEWS_LANGUAGE=en
NEWS_PAGE_SIZE=10

SUMMARY_MAX_TOKENS=120
SUMMARY_TEMPERATURE=0.1
SUMMARY_BATCH_SIZE=5
```

### 5. Run locally

```bash
streamlit run app.py
```

默认地址：

```text
http://localhost:8501
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `NEWS_API_KEY` | NewsAPI key | required |
| `DEEPSEEK_API_KEY` | DeepSeek API key | optional |
| `OPENAI_API_KEY` | OpenAI API key, used as fallback | optional |
| `DEEPSEEK_FLASH_MODEL` | Low-cost summary model | `deepseek-v4-flash` |
| `DEEPSEEK_PRO_MODEL` | High-quality summary model | `deepseek-v4-pro` |
| `DEEPSEEK_ADVANCED_MODE` | Enable pro mode | `false` |
| `OPENAI_MODEL` | Fallback OpenAI model | `gpt-4.1-mini` |
| `NEWS_LANGUAGE` | News language | `en` |
| `NEWS_PAGE_SIZE` | Max fetched news count | `10` |
| `SUMMARY_MAX_TOKENS` | Max output tokens per batch | `120` |
| `SUMMARY_TEMPERATURE` | Sampling temperature | `0.1` |
| `SUMMARY_BATCH_SIZE` | News count per batch request | `5` |

## Deployment

完整部署说明见：

[DEPLOYMENT.md](./DEPLOYMENT.md)

文档里包含：

- 本地部署
- Streamlit Community Cloud 部署
- 云服务器部署
- 环境变量配置
- 常见问题排查

## Performance Targets

在典型使用场景下，这个项目的工程目标是：

- API 调用次数减少约 80%
- token 消耗减少约 70%
- 页面响应速度明显提升

实际效果取决于：

- 新闻重复率
- 缓存积累规模
- 批处理大小
- 模型选择

## Roadmap

- 支持数据库持久化缓存
- 增加新闻来源过滤
- 增加多股票批量分析
- 增加定时任务和每日摘要邮件
- 接入价格走势做新闻与行情联动分析
- 增加 Docker 部署

## Resume Description

你可以在简历中这样描述这个项目：

> Built a financial news intelligence assistant with Python, Streamlit, NewsAPI, and LLM APIs. Implemented batch summarization, sentiment analysis, incremental updates, and local JSON caching to reduce repeated API calls and improve response speed.

## Contributing

欢迎基于这个项目继续扩展。提交 PR 前建议：

1. 保持现有 Streamlit UI 结构不被破坏
2. 保持缓存和批处理逻辑兼容
3. 为新增功能补充 README 或部署说明

## License

This project is licensed under the MIT License.
