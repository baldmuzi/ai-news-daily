# AI 行业快讯 · Claude Code 远程任务自动生成

## 线上链接
https://baldmuzi.github.io/ai-news-daily

## 架构

```
Claude Code 远程任务（定时/手动触发）
   │
   ├─ 技术频道任务
   │   ├─ 抓取 AI 技术资讯 → 生成 editions/edition-XXXX.html
   │   ├─ 重建 index.html（双频道入口首页）
   │   └─ 写 latest.json → push 到 main
   │
   └─ 产品/数据频道任务
       ├─ 抓取出海电商 AI 资讯 → 生成 business/edition-XXXX.html
       ├─ 重建 business/index.html（频道汇总页）
       └─ 写 latest-business.json → push 到 main
              │
              ▼
   GitHub Actions (notify.yml)
       ├─ 轮询页面 URL，等 HTTP 200 页面上线后
       ├─ 读 latest.json       → 推送技术群企业微信机器人
       └─ 读 latest-business.json → 推送产品群企业微信机器人
```

**职责分离：**
- 内容生成由 Claude Code 远程任务完成，不消耗 Actions 配额
- Actions 仅做"push 触发的通知器"，等页面上线后再推送，不会出现 404

---

## 站点地址

| 页面 | URL |
|------|-----|
| 双频道入口首页 | `https://baldmuzi.github.io/ai-news-daily/` |
| 技术频道汇总 | `https://baldmuzi.github.io/ai-news-daily/editions/` |
| 产品/数据频道汇总 | `https://baldmuzi.github.io/ai-news-daily/business/` |

---

## 部署步骤

### 1. 开启 GitHub Pages

Settings → Pages → Source: `Deploy from a branch` → `main` / `/ (root)` → Save

### 2. 配置 GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret：

| Secret | 用途 | 必填 |
|--------|------|------|
| `WECOM_WEBHOOK` | 技术群机器人 Webhook URL | ✅ |
| `WECOM_WEBHOOK_BUSINESS` | 产品/数据群机器人 Webhook URL | 可选 |
| `WECOM_MENTION_TECH` | 技术群艾特的成员 userid，逗号分隔 | 可选 |
| `WECOM_MENTION_MSG_TECH` | 技术群艾特后附加的一句话 | 可选 |
| `WECOM_MENTION_BUSINESS` | 产品群艾特的成员 userid，逗号分隔 | 可选 |
| `WECOM_MENTION_MSG_BUSINESS` | 产品群艾特后附加的一句话 | 可选 |

> `ANTHROPIC_API_KEY` 不需要配置，模型调用在 Claude Code 远程任务里完成。

企业微信 userid 查找：企业微信管理后台 → 通讯录 → 点开成员详情。艾特所有人用 `@all`。

### 3. 在 Claude Code 里创建两个远程任务

#### 技术频道任务 prompt

```
你是 AI 行业资讯编辑，面向软件工程师和技术研究者。
请在仓库根目录执行以下任务：

1. 通过 WebSearch / WebFetch 获取过去 24 小时内主流科技媒体的 AI 技术新闻
   重点来源：VentureBeat、TechCrunch、MIT Tech Review、OpenAI Blog、
   Anthropic Blog、HuggingFace Blog、量子位（技术向）

2. 挑选 Top 10 技术向新闻，每条用中文写 2-3 句技术点评

3. 提炼 5 个关键词标签、写 80 字以内本期导语

4. 计算期号：统计 editions/ 目录下 edition-*.html 文件数 + 1

5. 生成 editions/edition-XXXX.html，要求：
   - 暗色主题（背景 #080c14），蓝紫色调（--blue: #3b82f6）
   - Noto Serif SC + JetBrains Mono 字体，卡片式布局
   - 每张卡片：标题为可点击链接（href=原文URL，target="_blank"）、
     编辑点评、右下角"阅读原文 →"按钮（同样链接原文，target="_blank"）
   - 分类标签：模型前沿 / 软件开发 / 开源生态 / 行业政策 / 中国动态 / 其他

6. 重建根目录 index.html（双频道入口首页）：
   - 顶部展示两个频道入口卡片：
     「AI 技术快讯」→ 链接到 editions/ 最新一期
     「出海 AI 洞察」→ 链接到 business/index.html
   - 下方展示技术频道最近 10 期存档列表

7. 写 latest.json（用 json.dumps() 生成，禁止手拼字符串）：
   {
     "edition": "XXXX",
     "date": "YYYY年M月D日 HH:MM",
     "intro": "（80字内）",
     "tags": ["标签1","标签2","标签3","标签4","标签5"],
     "top3": [
       {"title": "新闻标题", "comment": "不超过60字，无换行无双引号"},
       {"title": "...", "comment": "..."},
       {"title": "...", "comment": "..."}
     ],
     "url": "https://baldmuzi.github.io/ai-news-daily/editions/edition-XXXX.html"
   }
   写完后验证：python3 -c "import json; json.load(open('latest.json'))"
   报错则重新生成

8. git remote set-url origin https://<TOKEN>@github.com/baldmuzi/ai-news-daily.git
   git add editions/ index.html latest.json
   git commit -m "feat: tech edition #XXXX"
   git push origin main
```

#### 产品/数据频道任务 prompt

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

5. 生成 business/edition-XXXX.html，要求：
   - 暗色主题（背景 #080c14），绿色调（--accent: #10b981）
   - 页头标题：「出海 AI 洞察」副标题：跨境电商 · 可持续发展 · AI 应用实战
   - 页头加「← 返回汇总」链接，href="../business/index.html"
   - 每张卡片：标题可点击（href=原文URL）、点评、"阅读原文 →"按钮
   - 分类标签：电商增长 / 可持续合规 / 消费洞察 / 营销工具 / 数据分析 / 供应链

6. 生成 business/index.html（频道汇总页）：
   - 绿色调，标题「出海 AI 洞察 · 往期存档」
   - 扫描 business/ 下所有 edition-*.html，按期号倒序，最多 20 期
   - 最新一期加高亮样式

7. 写 latest-business.json（用 json.dumps() 生成）：
   {
     "edition": "XXXX",
     "date": "YYYY年M月D日 HH:MM",
     "intro": "（80字内）",
     "tags": ["标签1","标签2","标签3","标签4","标签5"],
     "top3": [
       {"title": "标题（不含引号）", "comment": "不超过55字，无换行"},
       {"title": "...", "comment": "..."},
       {"title": "...", "comment": "..."}
     ],
     "url": "https://baldmuzi.github.io/ai-news-daily/business/edition-XXXX.html"
   }
   验证：python3 -c "import json; d=json.load(open('latest-business.json')); print('OK:', d['edition'])"

8. git remote set-url origin https://<TOKEN>@github.com/baldmuzi/ai-news-daily.git
   git add business/edition-XXXX.html business/index.html latest-business.json
   git commit -m "feat: business edition #XXXX"
   git push origin main
```

### 4. 设置定时

在 Claude Code 的 scheduled task 里配置 cron，建议两个频道错开时间：

| 频道 | 建议时间（北京时间） |
|------|------------------|
| 技术频道 | 每天 08:00 / 18:00 |
| 产品/数据频道 | 每天 09:00 / 19:00 |

---

## 文件职责

| 文件 | 由谁生成 | 作用 |
|------|---------|------|
| `index.html` | 技术频道任务 | 双频道入口首页 |
| `editions/edition-XXXX.html` | 技术频道任务 | 技术快讯各期内容 |
| `latest.json` | 技术频道任务 | 触发技术群企微通知 |
| `business/index.html` | 产品频道任务 | 产品频道汇总页 |
| `business/edition-XXXX.html` | 产品频道任务 | 出海洞察各期内容 |
| `latest-business.json` | 产品频道任务 | 触发产品群企微通知 |
| `.github/workflows/notify.yml` | 本仓库 | push 后等页面上线再推企微 |
| `.github/scripts/notify.py` | 本仓库 | 通知逻辑（轮询+发送+艾特） |

## JSON 结构参考

**latest.json / latest-business.json**
```json
{
  "edition": "0001",
  "date": "2026年5月8日 09:00",
  "intro": "本期导语...",
  "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
  "top3": [
    {"title": "新闻标题", "comment": "点评文字"},
    {"title": "...", "comment": "..."},
    {"title": "...", "comment": "..."}
  ],
  "url": "https://baldmuzi.github.io/ai-news-daily/editions/edition-0001.html"
}
```

## 企业微信机器人配置

群聊 → 右键 → 添加群机器人 → 新建 → 复制 Webhook URL → 填入对应 Secret。

企微通知效果：
```
AI 技术快讯 #0001 🤖
2026年5月8日 09:00 · 北京时间

本期导语...

关键词：Claude 4.7 · Cursor · 国产大模型 · AI 安全 · 融资

Top 3 速览：
> #1 Anthropic 发布 Claude 4.7
> 点评文字...

📖 阅读完整版

<@zhangsan> 今日技术快讯已更新
```
