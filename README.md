# AI 行业快讯 · 自动更新网站

自动爬取多路 RSS → Claude API 总结 Top 10 → 生成精美 HTML → 企业微信推送

## 项目结构

```
ai-news-daily/
├── generate.py              # 核心脚本
├── requirements.txt
├── index.html               # 自动生成的首页（存档列表）
├── editions/                # 每期 HTML 页面
│   ├── edition-0001.html
│   └── ...
└── .github/
    └── workflows/
        └── daily.yml        # GitHub Actions 定时任务
```

## 快速部署步骤

### 1. Fork / Clone 本仓库

```bash
git clone https://github.com/your-username/ai-news-daily
cd ai-news-daily
```

### 2. 配置 GitHub Secrets

在仓库 → Settings → Secrets and variables → Actions 中添加：

| 名称 | 说明 | 必填 |
|------|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API Key，从 console.anthropic.com 获取 | ✅ |
| `WECOM_WEBHOOK` | 企业微信机器人 Webhook URL | 可选 |

在 **Variables**（非 Secrets）中添加：

| 名称 | 示例值 |
|------|--------|
| `SITE_BASE_URL` | `https://your-username.github.io/ai-news-daily` |

### 3. 开启 GitHub Pages

Settings → Pages → Source 选择 `Deploy from a branch` → Branch: `main` / `/ (root)`

### 4. 手动触发第一次运行

Actions → "AI 行业快讯 · 每日自动更新" → Run workflow

稍等 1-2 分钟后访问 `https://your-username.github.io/ai-news-daily` 即可看到网站。

---

## 企业微信机器人配置

1. 在企业微信群中 → 右键群 → 添加群机器人 → 新建机器人
2. 复制 Webhook URL，格式为 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx`
3. 将此 URL 填入 GitHub Secrets `WECOM_WEBHOOK`

推送效果示例：
```
AI 行业快讯 #0005 🤖
2026年5月7日 12:00 · 北京时间

本期导语...

本期关键词：Anthropic超越OpenAI收入 · Cursor 3优化 · Claude Code登顶 · ...

Top 3 速览：
#01 Anthropic 年化收入超越 OpenAI...
...

📖 阅读完整版
```

---

## 定时调度说明

默认配置每天触发 3 次（北京时间 08:00 / 12:00 / 18:00）。
如需修改，编辑 `.github/workflows/daily.yml` 中的 `cron` 表达式。

```yaml
schedule:
  - cron: '0 0 * * *'   # UTC 00:00 = BJ 08:00
  - cron: '0 4 * * *'   # UTC 04:00 = BJ 12:00
  - cron: '0 10 * * *'  # UTC 10:00 = BJ 18:00
```

---

## 本地运行

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export WECOM_WEBHOOK="https://qyapi.weixin.qq.com/..."
export SITE_BASE_URL="http://localhost:8000"

python generate.py

# 预览
python -m http.server 8000
# 访问 http://localhost:8000
```

---

## 自定义 RSS 源

编辑 `generate.py` 顶部的 `RSS_SOURCES` 列表：

```python
RSS_SOURCES = [
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://www.technologyreview.com/feed/",
    # 添加你自己的 RSS 源...
]
```

推荐中文 AI 源：
- `https://rsshub.app/36kr/newsflashes` — 36氪快讯
- `https://rsshub.app/sspai/matrix` — 少数派
- `https://www.geekpark.net/rss` — 极客公园
