# Deployment Guide

本文档说明如何部署 `Financial News Intelligence Assistant`。

包含三种常见方式：

1. 本地运行
2. Streamlit Community Cloud 部署
3. 云服务器部署

## 1. Local Deployment

### Step 1: clone project

```bash
git clone <your-repo-url>
cd financial-news-intelligence-assistant
```

### Step 2: create virtual environment

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

### Step 3: install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: create `.env`

参考 `.env.example`：

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

### Step 5: start app

```bash
streamlit run app.py
```

浏览器访问：

```text
http://localhost:8501
```

## 2. Deploy on Streamlit Community Cloud

这是最适合个人作品展示的免费部署方式。

### Step 1: push code to GitHub

将项目推送到 GitHub 仓库，例如：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 2: log in to Streamlit Community Cloud

打开 Streamlit Community Cloud，使用 GitHub 账号登录。

### Step 3: create a new app

填写以下信息：

- Repository: 你的 GitHub 仓库
- Branch: `main`
- Main file path: `app.py`

### Step 4: configure secrets

在 Streamlit Cloud 的 `Secrets` 页面中填写：

```toml
NEWS_API_KEY="your_newsapi_key"
DEEPSEEK_API_KEY="your_deepseek_api_key"
OPENAI_API_KEY=""

DEEPSEEK_FLASH_MODEL="deepseek-v4-flash"
DEEPSEEK_PRO_MODEL="deepseek-v4-pro"
DEEPSEEK_ADVANCED_MODE="false"

OPENAI_MODEL="gpt-4.1-mini"
NEWS_LANGUAGE="en"
NEWS_PAGE_SIZE="10"

SUMMARY_MAX_TOKENS="120"
SUMMARY_TEMPERATURE="0.1"
SUMMARY_BATCH_SIZE="5"
```

可以直接参考：

[.streamlit/secrets.toml.example](./.streamlit/secrets.toml.example)

### Step 5: deploy

点击 `Deploy`，等待构建完成即可。

### Notes

- `analyzed_news.json` 在 Streamlit Cloud 上通常不是长期持久化存储
- 对于演示用途没有问题
- 如果你要做长期在线服务，建议把缓存迁移到数据库或对象存储

## 3. Deploy on a Cloud Server

适合需要更稳定运行或自定义域名的情况。

以下以 Linux 服务器为例。

### Step 1: connect to server

```bash
ssh user@your-server-ip
```

### Step 2: install Python

确保服务器安装 Python 3.10 或更高版本。

### Step 3: clone project

```bash
git clone <your-repo-url>
cd financial-news-intelligence-assistant
```

### Step 4: create venv and install packages

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 5: configure environment variables

在项目根目录创建 `.env`，内容与本地一致。

### Step 6: run app

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Optional: use nohup

```bash
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

### Optional: reverse proxy with Nginx

如果你有域名，可以让 Nginx 反向代理到 `8501` 端口。

典型思路：

- 外部访问 `https://your-domain.com`
- Nginx 转发到 `http://127.0.0.1:8501`

## Environment Strategy

推荐的模型策略：

- 默认模式：`deepseek-v4-flash`
- 高级模式：`deepseek-v4-pro`
- 兜底模式：`gpt-4.1-mini`

推荐的成本控制参数：

```env
SUMMARY_MAX_TOKENS=120
SUMMARY_TEMPERATURE=0.1
SUMMARY_BATCH_SIZE=5
```

## Cache Behavior

缓存文件：

```text
analyzed_news.json
```

行为说明：

- 已分析新闻优先命中缓存
- 新增新闻才会调用模型
- 缓存依据标题和文章指纹进行匹配

如果需要重置缓存，删除该文件即可。

## Troubleshooting

### 1. Streamlit page shows missing API key

检查 `.env` 或 Streamlit secrets 是否配置成功。

### 2. NewsAPI returns no data

可能原因：

- 股票代码太冷门
- 免费版 NewsAPI 有延迟
- 当前语言过滤过严

建议：

- 先测试 `AAPL`、`TSLA`、`NVDA`
- 将 `NEWS_LANGUAGE=en`

### 3. DeepSeek request fails

检查：

- `DEEPSEEK_API_KEY` 是否正确
- 模型名称是否填写正确
- 网络是否可访问对应 API

### 4. Cache seems not working

检查：

- 项目根目录是否生成 `analyzed_news.json`
- 是否每次都在同一个部署环境中运行
- 云平台文件系统是否会重置

### 5. NLTK download issue

首次运行可能需要下载 `vader_lexicon`。

如果环境限制外网，可以提前在本地准备好 NLTK 数据，或改为镜像源环境部署。

## Production Suggestions

如果你后续要把它做成长期服务，建议继续升级：

1. 将 JSON 缓存迁移到 SQLite / PostgreSQL
2. 增加定时任务，定期抓取新闻
3. 增加用户鉴权
4. 增加 Dockerfile 和 CI/CD
5. 增加监控和错误告警
