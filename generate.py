#!/usr/bin/env python3
"""
AI 行业快讯自动生成脚本
功能：爬取RSS → Claude API 总结 Top 10 → 生成 HTML → 企业微信通知
"""

import os
import json
import time
import datetime
import hashlib
import requests
import feedparser
import anthropic
from pathlib import Path
from zoneinfo import ZoneInfo

# ──────────────────────────────────────────────
# 配置区（也可通过环境变量覆盖）
# ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
WECOM_WEBHOOK   = os.environ.get("WECOM_WEBHOOK", "")   # 企业微信机器人 Webhook URL
SITE_BASE_URL   = os.environ.get("SITE_BASE_URL", "https://your-username.github.io/ai-news-daily")

RSS_SOURCES = [
    # 科技综合
    "https://feeds.feedburner.com/venturebeat/SZYF",          # VentureBeat AI
    "https://www.technologyreview.com/feed/",                   # MIT Tech Review
    "https://techcrunch.com/feed/",                             # TechCrunch
    # AI 专项
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    # 中文
    "https://www.36kr.com/feed",
    "https://rsshub.app/36kr/newsflashes",
]

MAX_ITEMS_PER_SOURCE = 15   # 每个源最多抓取条数
TOP_N               = 10    # 最终展示条数
FETCH_TIMEOUT       = 15    # RSS 抓取超时（秒）

# ──────────────────────────────────────────────
# 1. 抓取 RSS
# ──────────────────────────────────────────────
def fetch_rss_items(sources: list[str]) -> list[dict]:
    items = []
    cutoff = datetime.datetime.now(ZoneInfo("UTC")) - datetime.timedelta(hours=48)

    for url in sources:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        except Exception as e:
            print(f"[WARN] Failed to fetch {url}: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= MAX_ITEMS_PER_SOURCE:
                break

            # 解析发布时间
            pub = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = datetime.datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo("UTC"))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub = datetime.datetime(*entry.updated_parsed[:6], tzinfo=ZoneInfo("UTC"))

            if pub and pub < cutoff:
                continue

            summary = getattr(entry, "summary", "") or ""
            # 去除 HTML 标签（简单处理）
            import re
            summary = re.sub(r"<[^>]+>", " ", summary).strip()[:500]

            items.append({
                "title":   getattr(entry, "title", "Untitled"),
                "link":    getattr(entry, "link",  ""),
                "summary": summary,
                "pub":     pub.strftime("%Y-%m-%d %H:%M") if pub else "",
                "source":  feed.feed.get("title", url),
            })
            count += 1

    print(f"[INFO] Fetched {len(items)} items from {len(sources)} sources")
    return items


# ──────────────────────────────────────────────
# 2. Claude API 总结
# ──────────────────────────────────────────────
def summarize_with_claude(items: list[dict]) -> list[dict]:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # 构建输入文本
    news_text = "\n\n".join(
        f"[{i+1}] {it['title']}\n来源: {it['source']} | 时间: {it['pub']}\n摘要: {it['summary']}\n链接: {it['link']}"
        for i, it in enumerate(items)
    )

    prompt = f"""你是一位专注于 AI / 科技行业的资深编辑。以下是过去 48 小时内从多个科技媒体抓取的新闻条目：

{news_text}

请完成以下任务：
1. 从中挑选出最值得关注的 **Top {TOP_N}** 条新闻，优先考虑：
   - 重大技术突破或产品发布
   - 重要公司融资 / 收购
   - 行业政策与法规动态
   - 中国 AI 产业动态
2. 对每条新闻用中文写 2-3 句话的深度点评，点明为什么重要。
3. 为整期快讯提炼 5 个关键词标签（中文，每个不超过8字）。
4. 写一段 80 字以内的本期导语。

严格按以下 JSON 格式返回，不要输出任何其他内容：
{{
  "intro": "本期导语...",
  "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
  "items": [
    {{
      "rank": 1,
      "title": "新闻标题（可适当优化，保持准确）",
      "source": "来源媒体",
      "pub": "发布时间",
      "link": "原文链接",
      "comment": "编辑点评（2-3句）",
      "category": "模型前沿|软件开发|中国动态|行业政策|商业融资|产品发布|其他"
    }}
  ]
}}"""

    print("[INFO] Calling Claude API...")
    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()

    # 提取 JSON（有时模型会加代码块）
    import re
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("Claude 返回内容无法解析为 JSON")
    data = json.loads(m.group())
    print(f"[INFO] Got Top {len(data['items'])} items from Claude")
    return data


# ──────────────────────────────────────────────
# 3. 生成 HTML
# ──────────────────────────────────────────────
CATEGORY_COLORS = {
    "模型前沿": "#6366f1",
    "软件开发": "#06b6d4",
    "中国动态": "#f59e0b",
    "行业政策": "#10b981",
    "商业融资": "#ec4899",
    "产品发布": "#8b5cf6",
    "其他":     "#64748b",
}

def generate_html(data: dict, edition_num: int, output_path: Path):
    now_bj = datetime.datetime.now(ZoneInfo("Asia/Shanghai"))
    date_str = now_bj.strftime("%Y年%-m月%-d日")
    time_str = now_bj.strftime("%H:%M")
    iso_date = now_bj.strftime("%Y-%m-%d")
    filename  = f"edition-{edition_num:04d}.html"

    tags_html = "".join(
        f'<span class="tag">{t}</span>' for t in data["tags"]
    )

    items_html = ""
    for it in data["items"]:
        color = CATEGORY_COLORS.get(it.get("category", "其他"), "#64748b")
        items_html += f"""
        <article class="news-card" style="--accent:{color}">
          <div class="card-meta">
            <span class="rank">#{it['rank']:02d}</span>
            <span class="category-badge">{it.get('category','其他')}</span>
            <span class="source">{it['source']}</span>
            <span class="pub-time">{it['pub']}</span>
          </div>
          <h2 class="card-title">
            <a href="{it['link']}" target="_blank" rel="noopener">{it['title']}</a>
          </h2>
          <p class="card-comment">{it['comment']}</p>
          <a class="read-more" href="{it['link']}" target="_blank" rel="noopener">
            阅读原文 →
          </a>
        </article>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 行业快讯 #{edition_num:04d} · {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:       #080c14;
  --surface:  #0d1321;
  --border:   rgba(255,255,255,.07);
  --text:     #e2e8f0;
  --muted:    #64748b;
  --gold:     #f0b429;
  --blue:     #3b82f6;
  --glow:     rgba(59,130,246,.15);
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'Noto Sans SC', sans-serif;
  font-weight: 300;
  line-height: 1.7;
  min-height: 100vh;
  overflow-x: hidden;
}}

/* ── Starfield background ── */
body::before {{
  content: '';
  position: fixed; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 80% 50% at 20% 10%, rgba(59,130,246,.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 80%, rgba(99,102,241,.08) 0%, transparent 50%);
  pointer-events: none;
}}

.wrap {{ position: relative; z-index: 1; max-width: 860px; margin: 0 auto; padding: 0 24px 80px; }}

/* ── Header ── */
header {{
  padding: 64px 0 48px;
  text-align: center;
  border-bottom: 1px solid var(--border);
  margin-bottom: 48px;
}}
.header-label {{
  font-family: 'JetBrains Mono', monospace;
  font-size: .7rem;
  letter-spacing: .3em;
  color: var(--blue);
  text-transform: uppercase;
  margin-bottom: 20px;
  opacity: .8;
}}
header h1 {{
  font-family: 'Noto Serif SC', serif;
  font-size: clamp(2rem, 6vw, 3.2rem);
  font-weight: 700;
  letter-spacing: -.02em;
  background: linear-gradient(135deg, #e2e8f0 30%, #93c5fd 70%, #818cf8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 12px;
}}
.header-sub {{
  font-size: .85rem;
  color: var(--muted);
  letter-spacing: .05em;
}}
.header-date {{
  display: inline-flex; align-items: center; gap: 12px;
  margin-top: 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: .78rem;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 100px;
  padding: 6px 18px;
  background: rgba(255,255,255,.02);
}}
.header-date .dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--gold); animation: pulse 2s ease-in-out infinite; }}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.3}} }}

/* ── Intro ── */
.intro-box {{
  background: linear-gradient(135deg, rgba(59,130,246,.08), rgba(99,102,241,.06));
  border: 1px solid rgba(59,130,246,.2);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 32px;
  font-size: .95rem;
  color: #94a3b8;
  line-height: 1.8;
}}
.intro-box strong {{ color: var(--text); }}

/* ── Tags ── */
.tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 48px; }}
.tag {{
  font-size: .72rem;
  font-family: 'JetBrains Mono', monospace;
  padding: 4px 12px;
  border-radius: 100px;
  border: 1px solid var(--border);
  color: var(--muted);
  background: rgba(255,255,255,.02);
  transition: all .2s;
}}
.tag:hover {{ border-color: var(--blue); color: #93c5fd; }}

/* ── Section title ── */
.section-title {{
  font-family: 'JetBrains Mono', monospace;
  font-size: .68rem;
  letter-spacing: .25em;
  color: var(--muted);
  text-transform: uppercase;
  margin-bottom: 24px;
  display: flex; align-items: center; gap: 12px;
}}
.section-title::after {{ content:''; flex:1; height:1px; background:var(--border); }}

/* ── News Card ── */
.news-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 12px;
  padding: 28px 32px;
  margin-bottom: 20px;
  transition: transform .2s, box-shadow .2s, border-color .2s;
  position: relative;
  overflow: hidden;
}}
.news-card::before {{
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 60% 40% at 0% 50%, color-mix(in srgb, var(--accent) 8%, transparent), transparent);
  pointer-events: none;
}}
.news-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,.4);
  border-color: rgba(255,255,255,.12);
}}

.card-meta {{
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 12px;
}}
.rank {{
  font-family: 'JetBrains Mono', monospace;
  font-size: .65rem;
  font-weight: 600;
  color: var(--accent);
  opacity: .9;
}}
.category-badge {{
  font-size: .62rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent);
}}
.source {{ font-size: .72rem; color: var(--muted); }}
.pub-time {{ font-size: .68rem; color: var(--muted); margin-left: auto; font-family: 'JetBrains Mono', monospace; }}

.card-title {{
  font-family: 'Noto Serif SC', serif;
  font-size: 1.12rem;
  font-weight: 600;
  line-height: 1.5;
  margin-bottom: 12px;
}}
.card-title a {{ color: var(--text); text-decoration: none; transition: color .2s; }}
.card-title a:hover {{ color: #93c5fd; }}

.card-comment {{
  font-size: .875rem;
  color: #94a3b8;
  line-height: 1.75;
  margin-bottom: 16px;
  border-left: 2px solid var(--border);
  padding-left: 14px;
}}

.read-more {{
  font-family: 'JetBrains Mono', monospace;
  font-size: .68rem;
  letter-spacing: .05em;
  color: var(--blue);
  text-decoration: none;
  opacity: .7;
  transition: opacity .2s;
}}
.read-more:hover {{ opacity: 1; }}

/* ── Footer ── */
footer {{
  text-align: center;
  padding: 40px 0 0;
  border-top: 1px solid var(--border);
  font-size: .75rem;
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  line-height: 2;
}}
footer a {{ color: var(--blue); text-decoration: none; }}

/* ── Animations ── */
@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(20px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
.news-card {{ animation: fadeUp .4s ease both; }}
.news-card:nth-child(1)  {{ animation-delay: .05s }}
.news-card:nth-child(2)  {{ animation-delay: .10s }}
.news-card:nth-child(3)  {{ animation-delay: .15s }}
.news-card:nth-child(4)  {{ animation-delay: .20s }}
.news-card:nth-child(5)  {{ animation-delay: .25s }}
.news-card:nth-child(6)  {{ animation-delay: .30s }}
.news-card:nth-child(7)  {{ animation-delay: .35s }}
.news-card:nth-child(8)  {{ animation-delay: .40s }}
.news-card:nth-child(9)  {{ animation-delay: .45s }}
.news-card:nth-child(10) {{ animation-delay: .50s }}

@media (max-width: 600px) {{
  .news-card {{ padding: 20px; }}
  .pub-time {{ display: none; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="header-label">Edition #{edition_num:04d}</div>
    <h1>AI 行业快讯</h1>
    <div class="header-sub">聚焦软件开发 · 模型前沿 · 中国动态</div>
    <div class="header-date">
      <span class="dot"></span>
      {date_str} · 北京时间 {time_str}
    </div>
  </header>

  <div class="intro-box">{data['intro']}</div>

  <div class="tags">{tags_html}</div>

  <div class="section-title">Top {TOP_N} 精选快讯</div>

  <div class="news-list">
    {items_html}
  </div>

  <footer>
    <p>由 Claude AI 自动整理 · 每日更新</p>
    <p>数据来源：VentureBeat / MIT Tech Review / TechCrunch / OpenAI / Anthropic / HuggingFace / 36氪</p>
    <p style="margin-top:8px;opacity:.5;">Generated at {now_bj.strftime('%Y-%m-%d %H:%M:%S')} CST</p>
  </footer>
</div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"[INFO] HTML written → {output_path}")
    return filename


# ──────────────────────────────────────────────
# 4. 更新 index.html（历史存档列表）
# ──────────────────────────────────────────────
def update_index(editions_dir: Path, data_dir: Path):
    """扫描 editions/ 目录重建首页"""
    archives_file = data_dir / "archives.json"
    archives = []
    if archives_file.exists():
        archives = json.loads(archives_file.read_text())

    # 追加当前期
    latest = archives[-1] if archives else {}

    # 读最新 edition HTML 文件列表
    html_files = sorted(editions_dir.glob("edition-*.html"), reverse=True)

    cards_html = ""
    for i, f in enumerate(html_files[:20]):
        num = int(f.stem.split("-")[1])
        mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime, tz=ZoneInfo("Asia/Shanghai"))
        label = "最新一期" if i == 0 else f"#{num:04d}"
        cls = "latest" if i == 0 else ""
        cards_html += f"""
      <a class="edition-card {cls}" href="editions/{f.name}">
        <span class="ed-num">{num:02d}</span>
        <div class="ed-info">
          <div class="ed-title">AI 行业快讯 Top 10</div>
          <div class="ed-date">{mtime.strftime('%Y年%-m月%-d日 %H:%M')}</div>
        </div>
        <span class="ed-arrow">→</span>
      </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 行业快讯</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@700&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@300;400&display=swap" rel="stylesheet">
<style>
:root{{--bg:#080c14;--surface:#0d1321;--border:rgba(255,255,255,.07);--text:#e2e8f0;--muted:#64748b;--blue:#3b82f6;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:'Noto Sans SC',sans-serif;font-weight:300;}}
body::before{{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 20% 10%,rgba(59,130,246,.1) 0%,transparent 60%),radial-gradient(ellipse 60% 40% at 80% 80%,rgba(99,102,241,.07) 0%,transparent 50%);pointer-events:none;}}
.wrap{{position:relative;z-index:1;max-width:760px;margin:0 auto;padding:0 24px 80px;}}
header{{padding:64px 0 48px;text-align:center;border-bottom:1px solid var(--border);margin-bottom:48px;}}
.label{{font-family:'JetBrains Mono',monospace;font-size:.68rem;letter-spacing:.3em;color:var(--blue);text-transform:uppercase;margin-bottom:16px;}}
h1{{font-family:'Noto Serif SC',serif;font-size:clamp(2rem,6vw,3rem);background:linear-gradient(135deg,#e2e8f0 30%,#93c5fd 70%,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px;}}
.sub{{font-size:.82rem;color:var(--muted);letter-spacing:.08em;}}
.section-title{{font-family:'JetBrains Mono',monospace;font-size:.65rem;letter-spacing:.25em;color:var(--muted);text-transform:uppercase;margin-bottom:20px;display:flex;align-items:center;gap:12px;}}
.section-title::after{{content:'';flex:1;height:1px;background:var(--border);}}
.edition-card{{display:flex;align-items:center;gap:20px;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:14px;text-decoration:none;color:var(--text);transition:transform .2s,border-color .2s;}}
.edition-card:hover{{transform:translateY(-2px);border-color:rgba(59,130,246,.3);}}
.edition-card.latest{{border-color:rgba(59,130,246,.25);background:linear-gradient(135deg,rgba(59,130,246,.06),rgba(99,102,241,.04));}}
.ed-num{{font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:600;color:rgba(99,102,241,.4);min-width:48px;text-align:center;}}
.ed-title{{font-size:.92rem;font-weight:400;margin-bottom:4px;}}
.ed-date{{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:var(--muted);}}
.ed-arrow{{margin-left:auto;font-size:.9rem;color:var(--blue);opacity:.5;}}
footer{{text-align:center;padding:32px 0 0;border-top:1px solid var(--border);font-size:.72rem;color:var(--muted);font-family:'JetBrains Mono',monospace;line-height:2;}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="label">Daily Newsletter</div>
    <h1>AI 行业快讯</h1>
    <div class="sub">聚焦软件开发 · 模型前沿 · 中国动态</div>
  </header>
  <div class="section-title">往期存档</div>
  <div>{cards_html}</div>
  <footer>
    <p>由 Claude AI 自动整理 · 每日多次更新</p>
    <p style="margin-top:4px;opacity:.5;">Powered by Anthropic Claude + GitHub Actions</p>
  </footer>
</div>
</body>
</html>"""

    (data_dir / "index.html").write_text(index_html, encoding="utf-8")
    print("[INFO] index.html updated")


# ──────────────────────────────────────────────
# 5. 企业微信通知
# ──────────────────────────────────────────────
def send_wecom(data: dict, edition_num: int, site_url: str):
    if not WECOM_WEBHOOK:
        print("[INFO] WECOM_WEBHOOK not set, skipping notification")
        return

    now_bj = datetime.datetime.now(ZoneInfo("Asia/Shanghai"))
    tags_str = " · ".join(data["tags"])
    top3 = data["items"][:3]
    top3_text = "\n".join(
        f"> **#{it['rank']} {it['title']}**\n> {it['comment'][:60]}..."
        for it in top3
    )
    edition_url = f"{site_url}/editions/edition-{edition_num:04d}.html"

    msg = f"""**AI 行业快讯 #{edition_num:04d}** 🤖
{now_bj.strftime('%Y年%-m月%-d日 %H:%M')} · 北京时间

{data['intro']}

**本期关键词：** {tags_str}

**Top 3 速览：**
{top3_text}

[📖 阅读完整版]({edition_url})"""

    payload = {
        "msgtype": "markdown",
        "markdown": {"content": msg}
    }
    try:
        r = requests.post(WECOM_WEBHOOK, json=payload, timeout=10)
        result = r.json()
        if result.get("errcode") == 0:
            print("[INFO] 企业微信通知发送成功")
        else:
            print(f"[WARN] 企业微信返回异常: {result}")
    except Exception as e:
        print(f"[WARN] 企业微信发送失败: {e}")


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main():
    root = Path(__file__).parent
    editions_dir = root / "editions"
    editions_dir.mkdir(exist_ok=True)

    # 计算期号
    existing = list(editions_dir.glob("edition-*.html"))
    edition_num = len(existing) + 1

    # Step 1: 抓取
    items = fetch_rss_items(RSS_SOURCES)
    if not items:
        print("[ERROR] No items fetched, aborting")
        return

    # Step 2: Claude 总结
    data = summarize_with_claude(items)

    # Step 3: 生成 HTML
    out_path = editions_dir / f"edition-{edition_num:04d}.html"
    generate_html(data, edition_num, out_path)

    # Step 4: 更新首页
    update_index(editions_dir, root)

    # Step 5: 企业微信通知
    send_wecom(data, edition_num, SITE_BASE_URL)

    print(f"[DONE] Edition #{edition_num} generated successfully!")


if __name__ == "__main__":
    main()
