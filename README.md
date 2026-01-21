# 🤖 AI News Collector & Digest

一个自动化的 AI 新闻收集工具。每天定时从 Hacker News 和 Reddit 抓取最新的 AI/LLM 相关讨论，使用 GPT-4/Claude 生成中文摘要和评分，并整理成 Obsidian 友好的 Markdown 日报。

## ✨ 特性

- **多源采集**: 支持 Hacker News (API) 和 Reddit (PRAW)。
- **智能处理**:
  - 自动翻译标题为中文。
  - 生成 50-80 字的核心摘要。
  - 自动提取标签 (Tags) 和分类 (Category)。
  - 基于 AI 评分 (1-5星) 进行排序。
- **Markdown 输出**: 生成格式整洁的 `.md` 文件，完美适配 Obsidian。
- **自动化部署**: 内置 GitHub Actions 配置，支持每日定时运行并自动 Commit 同步。

## 🚀 快速开始 (本地运行)

### 1. 安装依赖
需要 Python 3.8+。
```bash
pip install -r requirements.txt
```

### 2. 配置环境
复制配置文件模板并填入您的 API Keys：
```bash
cp .env.example .env
# 编辑 .env 文件，填入 OPENAI_API_KEY 等
```

### 3. 运行
```bash
python src/main.py
```
运行完成后，生成的日报将保存在 `news/` 目录下。

## ☁️ 部署到 GitHub Actions (推荐)

本项目设计为可以在 GitHub Actions 上完全自动化运行，通过 Git 仓库同步 Markdown 文件。

1. **Push 代码**: 将本项目推送到您的 GitHub 仓库。
2. **配置 Secrets**: 在仓库 Settings -> Secrets and variables -> Actions 中添加：
    - `OPENAI_API_KEY`: (必填) OpenAI API Key
    - `REDDIT_CLIENT_ID`: (可选) Reddit Script App ID
    - `REDDIT_CLIENT_SECRET`: (可选) Reddit Script App Secret
    - `REDDIT_USER_AGENT`: (可选) e.g., `python:ai-news:v1`
3. **自动运行**:
    - 脚本默认在每天 **UTC 0:00** (北京时间 8:00) 自动触发。
    - 您也可以在 Actions 页面手动点击 "Run workflow" 触发。

## 📂 项目结构

```
.
├── src/
│   ├── collector.py    # 数据采集 (HN/Reddit)
│   ├── processor.py    # AI 处理 (OpenAI API)
│   ├── publisher.py    # Markdown 渲染
│   └── main.py         # 程序入口
├── templates/
│   └── daily_digest.md.j2  # Jinja2 模板
├── news/               # 自动生成的日报文件
└── .github/workflows/  # CI/CD 配置
```

## 🛠️ 自定义

- **修改关键词**: 编辑 `src/collector.py` 中的 `self.keywords` 列表。
- **修改排版**: 编辑 `templates/daily_digest.md.j2` 模板文件。
- **修改模型**: 在 Secrets 或 `.env` 中设置 `OPENAI_MODEL` (默认 gpt-4o)。

## License
MIT
