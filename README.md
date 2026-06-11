# 早报中心 · AI & 趋势自动生成

## 线上链接
https://baldmuzi.github.io/ai-news-daily

## 架构

```
Claude Code 远程任务（多个频道独立运行）
   │
   ├─ 技术频道任务
   │   ├─ editions/edition-XXXX.html
   │   ├─ editions/index.html
   │   └─ latest.json → push
   │
   ├─ 产品/数据频道任务
   │   ├─ business/edition-XXXX.html
   │   ├─ business/index.html
   │   └─ latest-business.json → push
   │
   ├─ 运动健康频道任务（Fanka）
   │   ├─ fitness/edition-XXXX.html
   │   ├─ fitness/index.html
   │   └─ latest-fitness.json → push
   │
   ├─ 社交趋势频道任务（Fanka）
   │   ├─ fanka-social/edition-XXXX.html
   │   ├─ fanka-social/index.html
   │   └─ latest-fanka-social.json → push
   │
   └─ VIVAIA 品牌趋势任务
       ├─ vivaia/edition-XXXX.html
       ├─ vivaia/index.html
       └─ latest-vivaia.json → push
              │
              ▼
   GitHub Actions (notify.yml)
       ├─ 轮询对应页面 URL，等 HTTP 200 上线后
       ├─ latest.json          → 技术群企微机器人
       ├─ latest-business.json → 产品群企微机器人
       ├─ latest-fitness.json      → Fanka 群企微机器人
       ├─ latest-fanka-social.json → Fanka 社交趋势企微机器人
       └─ latest-vivaia.json       → VIVAIA 群企微机器人
```

- 根目录 `index.html` 为**静态门户首页**，不由任务生成，直接维护
- 每个频道只管自己的子目录，互不干扰

---

## 站点地址

| 页面 | URL |
|------|-----|
| 门户首页 | `https://baldmuzi.github.io/ai-news-daily/` |
| 技术频道存档 | `https://baldmuzi.github.io/ai-news-daily/editions/` |
| 产品/数据频道存档 | `https://baldmuzi.github.io/ai-news-daily/business/` |
| 运动健康频道存档 | `https://baldmuzi.github.io/ai-news-daily/fitness/` |
| Fanka 社交趋势存档 | `https://baldmuzi.github.io/ai-news-daily/fanka-social/` |
| VIVAIA 品牌趋势存档 | `https://baldmuzi.github.io/ai-news-daily/vivaia/` |

---

## 部署步骤

### 1. 开启 GitHub Pages

Settings → Pages → Source: `Deploy from a branch` → `main` / `/ (root)` → Save

### 2. 配置 GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret：

| Secret | 用途 | 必填 |
|--------|------|------|
| `WECOM_WEBHOOK` | 技术群机器人 Webhook | ✅ |
| `WECOM_WEBHOOK_BUSINESS` | 产品/数据群机器人 Webhook | 可选 |
| `WECOM_WEBHOOK_FITNESS` | Fanka 运动健康群机器人 Webhook | 可选 |
| `WECOM_WEBHOOK_FANKA_SOCIAL` | Fanka 社交趋势群机器人 Webhook；未配置时回退到 `WECOM_WEBHOOK_FITNESS` | 可选 |
| `WECOM_WEBHOOK_VIVAIA` | VIVAIA 群机器人 Webhook | 可选 |
| `WECOM_MENTION_TECH` | 技术群艾特成员 userid（逗号分隔） | 可选 |
| `WECOM_MENTION_MSG_TECH` | 技术群艾特后附加的话 | 可选 |
| `WECOM_MENTION_BUSINESS` | 产品群艾特成员 userid | 可选 |
| `WECOM_MENTION_MSG_BUSINESS` | 产品群艾特后附加的话 | 可选 |
| `WECOM_MENTION_FITNESS` | Fanka 群艾特成员 userid | 可选 |
| `WECOM_MENTION_MSG_FITNESS` | Fanka 群艾特后附加的话 | 可选 |
| `WECOM_MENTION_FANKA_SOCIAL` | Fanka 社交趋势群艾特成员 userid；未配置时回退到 `WECOM_MENTION_FITNESS` | 可选 |
| `WECOM_MENTION_MSG_FANKA_SOCIAL` | Fanka 社交趋势群艾特后附加的话 | 可选 |
| `WECOM_MENTION_VIVAIA` | VIVAIA 群艾特成员 userid | 可选 |
| `WECOM_MENTION_MSG_VIVAIA` | VIVAIA 群艾特后附加的话 | 可选 |

> 企微 userid：企业微信管理后台 → 通讯录 → 成员详情。艾特全员用 `@all`。

### 3. 在 Claude Code 里创建远程任务

---

#### 📡 技术频道 prompt

```
你是 AI 行业资讯编辑，面向软件工程师和技术研究者。
请在仓库根目录执行以下任务：

1. 通过 WebSearch / WebFetch 获取过去 24 小时内的 AI 技术新闻
   重点来源：VentureBeat、TechCrunch、MIT Tech Review、OpenAI Blog、
   Anthropic Blog、HuggingFace Blog、量子位（技术向）

2. 挑选 Top 10，每条用中文写 2-3 句技术点评

3. 提炼 5 个关键词标签、写 80 字以内本期导语

4. 计算期号：统计 editions/ 目录下 edition-*.html 文件数 + 1

5. 生成 editions/edition-XXXX.html：
   - 暗色主题（背景 #080c14），蓝紫色调（--blue: #3b82f6）
   - Noto Serif SC + JetBrains Mono 字体，卡片式布局
   - 每张卡片：标题为可点击链接（target="_blank"）、点评、"阅读原文 →"按钮
   - 页头加「← 返回存档」链接，href="../editions/"
   - 分类标签：模型前沿 / 软件开发 / 开源生态 / 行业政策 / 中国动态 / 其他

6. 重建 editions/index.html（技术频道存档页）：
   - 蓝紫色调，标题「AI 技术快讯 · 往期存档」
   - 扫描 editions/ 下所有 edition-*.html，按期号倒序，最多 20 期
   - 最新一期加高亮，顶部加「← 返回首页」链接，href="../"

7. 写 latest.json（用 json.dumps() 生成，禁止手拼字符串）：
   {
     "edition": "XXXX",
     "date": "YYYY年M月D日 HH:MM",
     "intro": "（80字内）",
     "tags": ["标签1","标签2","标签3","标签4","标签5"],
     "top3": [
       {"title": "新闻标题", "comment": "不超过60字，无换行无双引号", "url": "原文URL"},
       {"title": "...", "comment": "...", "url": "..."},
       {"title": "...", "comment": "...", "url": "..."}
     ],
     "url": "https://baldmuzi.github.io/ai-news-daily/editions/edition-XXXX.html"
   }
   验证：python3 -c "import json; json.load(open('latest.json'))"

8. git remote set-url origin https://<TOKEN>@github.com/baldmuzi/ai-news-daily.git
   git add editions/ latest.json
   git commit -m "feat: tech edition #XXXX"
   git push origin main
```

---

#### 🌏 产品/数据频道 prompt（出海环保鞋类电商）

```
你是一位服务于中国出海环保鞋类电商公司的 AI 产品与数据洞察编辑。
读者是产品经理和数据分析师。
请在仓库根目录执行以下任务：

1. 用以下搜索词分别搜索，每组取最新 3-5 条：
   - "AI e-commerce 2026"
   - "AI sustainability supply chain 2026"
   - "AI consumer behavior retail 2026"
   - "AI cross-border ecommerce tools 2026"
   - "AI data analytics marketing 2026"
   - "人工智能 跨境电商 2026"
   优先来源：VentureBeat、TechCrunch、a16z Blog、36氪、量子位、
   亿邦动力、雨果跨境、Modern Retail、Retail Dive

2. 筛选 Top 10（每条必须有明确 AI 技术应用，至少 4 条与电商相关、
   至少 1 条与 ESG/环保相关、至少 1 条来自中文媒体）
   每条点评格式：
   【是什么】AI 做了什么
   【对我们意味着什么】对出海鞋类 PM 或数据分析师的直接价值

3. 提炼 5 个关键词标签、写 80 字以内导语

4. 计算期号：统计 business/ 目录下 edition-*.html 文件数 + 1

5. 生成 business/edition-XXXX.html：
   - 暗色主题（背景 #080c14），绿色调（--accent: #10b981）
   - 页头标题「出海 AI 洞察」副标题：跨境电商 · 可持续发展 · AI 应用实战
   - 页头加「← 返回存档」链接，href="../business/"
   - 每张卡片：标题可点击（href=原文URL）、点评、"阅读原文 →"按钮
   - 分类标签：电商增长 / 可持续合规 / 消费洞察 / 营销工具 / 数据分析 / 供应链

6. 重建 business/index.html（频道存档页）：
   - 绿色调，标题「出海 AI 洞察 · 往期存档」
   - 扫描 business/ 下所有 edition-*.html，按期号倒序，最多 20 期
   - 最新一期加高亮，顶部加「← 返回首页」链接，href="../"

7. 写 latest-business.json（用 json.dumps() 生成）：
   {
     "edition": "XXXX",
     "date": "YYYY年M月D日 HH:MM",
     "intro": "（80字内）",
     "tags": ["标签1","标签2","标签3","标签4","标签5"],
     "top3": [
       {"title": "标题（不含引号）", "comment": "不超过55字，无换行", "url": "原文URL"},
       {"title": "...", "comment": "...", "url": "..."},
       {"title": "...", "comment": "...", "url": "..."}
     ],
     "url": "https://baldmuzi.github.io/ai-news-daily/business/edition-XXXX.html"
   }
   验证：python3 -c "import json; d=json.load(open('latest-business.json')); print('OK:', d['edition'])"

8. git remote set-url origin https://<TOKEN>@github.com/baldmuzi/ai-news-daily.git
   git add business/ latest-business.json
   git commit -m "feat: business edition #XXXX"
   git push origin main
```

---

#### 🏃‍♀️ 运动健康频道 prompt（Fanka）

```
你是 Fanka 品牌的运动健康趋势编辑。Fanka 是一家中国出海全球的女性压缩服品牌，
核心理念是「让运动变得更简单」。读者是品牌经理和内容运营，
需要紧跟全球最新运动方式和健康趋势，以此为素材制作内容。
请在仓库根目录执行以下任务：

1. 用以下搜索词分别搜索，每组取最新 3-5 条：
   - "fitness trend 2026" 或 "workout trend 2026"
   - "wellness trend women 2026"
   - "new exercise viral 2026"（TikTok/Instagram 爆款运动）
   - "activewear compression wear trend 2026"
   - "women sports lifestyle 2026"
   - "运动健康趋势 2026" 或 "健身潮流 2026"（中文内容）
   优先来源：Well+Good、Women's Health、Shape、Runner's World、
   Business of Fashion（athleisure）、Mintel、Euromonitor、
   TikTok 热搜、小红书/抖音趋势、36氪健康、虎嗅

2. 筛选 Top 10，每条用中文写 2-3 句点评，格式：
   【趋势是什么】具体是什么新运动/健康方式，哪里流行起来的
   【内容机会】Fanka 品牌经理或内容运营可以怎么借势做内容

   筛选偏好：
   - 优先选择有病毒式传播潜力的新兴运动方式（如当年 Hot Girl Walk、12-3-30 等）
   - 优先选择与压缩服/运动内衣/紧身裤相关的穿搭或功能性趋势
   - 优先选择女性主导的运动文化内容
   - 包含至少 1 条来自中文平台（小红书/抖音）的趋势

3. 提炼 5 个关键词标签（中文，不超过 8 字，如"普拉提热潮""户外徒步穿搭""恢复性运动"）
   写 80 字以内导语，体现：全球视野 + Fanka 内容创作机会

4. 计算期号：统计 fitness/ 目录下 edition-*.html 文件数 + 1

5. 生成 fitness/edition-XXXX.html：
   - 暗色主题（背景 #080c14），玫瑰红色调（--accent: #f43f5e）
   - Noto Serif SC + JetBrains Mono 字体，卡片式布局
   - 页头主标题：「运动健康趋势」
     副标题：Global Fitness & Wellness · Powered by Fanka
   - 页头加「← 返回存档」链接，href="../fitness/"
   - 每张卡片：标题为可点击链接（href=原文URL，target="_blank"）、
     点评（含【趋势是什么】+【内容机会】）、"查看原文 →"按钮
   - 分类标签：新兴运动 / 穿搭趋势 / 健康生活 / 社媒热点 / 市场洞察 / 女性运动

6. 重建 fitness/index.html（频道存档页）：
   - 玫瑰红色调，标题「运动健康趋势 · 往期存档」
   - 扫描 fitness/ 下所有 edition-*.html，按期号倒序，最多 20 期
   - 最新一期加高亮，顶部加「← 返回首页」链接，href="../"

7. 写 latest-fitness.json（用 json.dumps() 生成，禁止手拼字符串）：
   {
     "edition": "XXXX",
     "date": "YYYY年M月D日 HH:MM",
     "intro": "（80字内，体现 Fanka 内容视角）",
     "tags": ["标签1","标签2","标签3","标签4","标签5"],
     "top3": [
       {"title": "趋势标题（不含引号）", "comment": "不超过55字，无换行", "url": "原文URL"},
       {"title": "...", "comment": "...", "url": "..."},
       {"title": "...", "comment": "...", "url": "..."}
     ],
     "url": "https://baldmuzi.github.io/ai-news-daily/fitness/edition-XXXX.html"
   }
   验证：python3 -c "import json; d=json.load(open('latest-fitness.json')); print('OK:', d['edition'])"

8. git remote set-url origin https://<TOKEN>@github.com/baldmuzi/ai-news-daily.git
   git add fitness/ latest-fitness.json
   git commit -m "feat: fitness edition #XXXX"
   git push origin main
   echo "pushed: fitness/edition-XXXX.html fitness/index.html latest-fitness.json"
```

---

#### Fanka 社交趋势拆解 prompt

完整提示词见 `prompts/fanka-social-trends-daily.md`。

该任务独立生成：

- `fanka-social/edition-XXXX.html`
- `fanka-social/index.html`
- `latest-fanka-social.json`

它专门抓取 TikTok、Instagram、小红书、抖音、Reddit、Amazon reviews、Google 推荐搜索词等社交与用户反馈信号，并拆解 the_french_fit、Alo Yoga、Buff Bunny、Sweaty Betty、Vuori、Gymshark、Halara 等头部账号或竞品的内容结构。

---

### 4. 设置定时（建议错开时间）

| 频道 | 建议时间（北京时间） |
|------|------------------|
| 技术频道 | 每天 08:00 / 18:00 |
| 产品/数据频道 | 每天 09:00 / 19:00 |
| 运动健康频道 | 每天 08:30 / 18:30 |
| Fanka 社交趋势频道 | 每天 10:00 / 20:00 |

---

## 文件职责

| 文件 | 由谁生成 | 说明 |
|------|---------|------|
| `index.html` | **静态文件（手动维护）** | 门户首页，展示所有频道入口 |
| `editions/edition-XXXX.html` | 技术频道任务 | 技术快讯各期 |
| `editions/index.html` | 技术频道任务 | 技术频道存档页 |
| `latest.json` | 技术频道任务 | 触发技术群企微 |
| `business/edition-XXXX.html` | 产品频道任务 | 出海洞察各期 |
| `business/index.html` | 产品频道任务 | 产品频道存档页 |
| `latest-business.json` | 产品频道任务 | 触发产品群企微 |
| `fitness/edition-XXXX.html` | Fanka 任务 | 运动健康趋势各期 |
| `fitness/index.html` | Fanka 任务 | 运动健康存档页 |
| `latest-fitness.json` | Fanka 任务 | 触发 Fanka 群企微 |
| `fanka-social/edition-XXXX.html` | Fanka 社交趋势任务 | 社交趋势拆解各期 |
| `fanka-social/index.html` | Fanka 社交趋势任务 | 社交趋势存档页 |
| `latest-fanka-social.json` | Fanka 社交趋势任务 | 触发 Fanka 社交趋势企微 |
| `.github/workflows/notify.yml` | 本仓库 | 多频道 push 触发通知 |
| `.github/scripts/notify.py` | 本仓库 | 轮询+发送+艾特逻辑 |

## JSON 结构

```json
{
  "edition": "0001",
  "date": "2026年5月9日 08:30",
  "intro": "本期导语...",
  "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
  "top3": [
    {"title": "标题", "comment": "点评", "url": "原文URL"},
    {"title": "...", "comment": "...", "url": "..."},
    {"title": "...", "comment": "...", "url": "..."}
  ],
  "url": "https://baldmuzi.github.io/ai-news-daily/fitness/edition-0001.html"
}
```

## 企微通知格式

```
# Fanka 运动健康趋势 #0001 🤖
2026年5月9日 08:30 · 北京时间

本期导语...

关键词：普拉提热潮 · 户外徒步穿搭 · 恢复性运动 · 社媒健身 · 女性运动文化

Top 3 速览：
> **#1** | [趋势标题](原文URL)
> 点评内容...

[📖 阅读完整版](https://baldmuzi.github.io/ai-news-daily/fitness/edition-0001.html)

<@wangwu> 今日运动趋势已更新，请查阅！
```
