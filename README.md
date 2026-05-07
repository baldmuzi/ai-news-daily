# AI 行业快讯 · Claude Code 远程任务自动生成

## 架构

```
Claude Code 远程任务 (定时/手动触发)
   │
   ├─ 1. 抓取 / 分析最新 AI 资讯
   ├─ 2. 生成 editions/edition-XXXX.html
   ├─ 3. 更新 index.html
   ├─ 4. 写 latest.json（含期号、导语、Top3、URL）
   └─ 5. git commit + push 到 main
              │
              ▼
   GitHub Actions (notify.yml)
              │
              └─ 读 latest.json → 推送企业微信群机器人
```

**职责分离：**
- 内容生成在 Claude Code 远程任务里完成（不消耗 Actions 配额、不用部署 Python）
- Actions 只做"push 触发的通知器"，逻辑简单稳定

---

## 你需要做的步骤

### 1. 配置仓库 Secrets

Settings → Secrets and variables → Actions → New repository secret：

| 名称 | 用途 |
|------|------|
| `WECOM_WEBHOOK` | 企业微信群机器人 webhook URL |

> 不需要 `ANTHROPIC_API_KEY`，因为模型调用在 Claude Code 远程任务里完成，不在 Actions 里跑。

### 2. （可选）开启 GitHub Pages

Settings → Pages → Source: `Deploy from a branch` → 选 `main` / `/ (root)`。
启用后访问地址形如 `https://<user>.github.io/<repo>/editions/edition-0001.html`，这个 URL 也是 `latest.json` 里 `url` 字段要写的值。

### 3. 配置 Claude Code 远程任务

在 Claude Code 里创建 remote task（或 scheduled task），prompt 模板：

```
你是 AI 行业资讯编辑。请在仓库根目录执行：

1. 通过 WebSearch / WebFetch 获取过去 24 小时内主流科技媒体的 AI 相关新闻
   （VentureBeat / TechCrunch / MIT Tech Review / OpenAI Blog / Anthropic / 36氪 等）
2. 挑选 Top 10，每条写 2-3 句中文点评
3. 提炼 5 个关键词标签、写 80 字以内本期导语
4. 计算期号 = editions/ 目录下已有 edition-*.html 文件数 + 1（首次为 0001）
5. 生成 editions/edition-XXXX.html（暗色主题、Noto Serif SC + JetBrains Mono 字体、卡片式布局）
6. 重建 index.html（往期存档首页，最多展示 20 期）
7. 写 latest.json（结构见 README）
8. git add . && git commit -m "feat: edition #XXXX" && git push origin main
```

要点：
- 远程任务环境需有 push 到 main 的权限（Claude Code remote 默认通过 GitHub 授权即可）
- 修改到 `latest.json` 或 `editions/**` 任一文件都会触发 Actions

### 4. （可选）让远程任务定时跑

在 Claude Code 的 scheduled task 里配置 cron，例如北京时间每天 08:00 / 12:00 / 18:00 各跑一次。

### 5. 首次验证

1. 手动跑一次 Claude Code 远程任务
2. 确认仓库出现 `editions/edition-0001.html` / `index.html` / `latest.json`
3. 看 GitHub Actions → "Notify WeCom on new edition" 自动触发并成功
4. 企微群收到机器人消息

---

## 文件职责

| 文件 | 谁写 | 作用 |
|------|------|------|
| `editions/edition-XXXX.html` | Claude Code 远程任务 | 当期完整页面 |
| `index.html` | Claude Code 远程任务 | 往期存档首页 |
| `latest.json` | Claude Code 远程任务 | 给 Actions 读的最新摘要（推企微用） |
| `.github/workflows/notify.yml` | 已就位 | push 触发时推企微 |

## latest.json 结构

```json
{
  "edition": "0001",
  "date": "2026年5月7日 12:00",
  "intro": "本期聚焦 Claude 4.7 发布与中国大模型新动向...",
  "tags": ["Claude 4.7", "Cursor", "国产大模型", "AI 安全", "融资"],
  "top3": [
    {"title": "Anthropic 发布 Claude 4.7", "comment": "..."},
    {"title": "...", "comment": "..."},
    {"title": "...", "comment": "..."}
  ],
  "url": "https://your-user.github.io/ai-news-daily/editions/edition-0001.html"
}
```

## 企业微信机器人

群聊 → 右键 → 添加群机器人 → 新建 → 复制 Webhook URL → 填到 Secret `WECOM_WEBHOOK`。
