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
| Fanka 舆情巡查看板 | `https://baldmuzi.github.io/ai-news-daily/fanka-patrol/` |
| VIVAIA 品牌趋势存档 | `https://baldmuzi.github.io/ai-news-daily/vivaia/` |

---

## 部署步骤

### Fanka 舆情巡查频道

`fanka-patrol/` 使用“全部记录主看板 + 每日巡查存档 + 每次独立存档”，不沿用固定条数的内容日报。它关注 Fanka 自身的公开评价与讨论，与 `fanka-social/` 的社交趋势拆解分开。

- `fanka-patrol/data/YYYY-MM-DD-NNN.json`：每次巡查的证据数据。首版复用 2026-11-10 本聊天已实际读取的 6 条网页样本，不声称新增全量采集。
- `fanka-patrol/index.html`：汇总所有巡查，按最近巡查日期和当日序号倒序展示，支持关键词、平台、内容类型、评价倾向、最近巡查日期及待复核筛选。同一原文 URL 合并为一张卡片，展示最新观察，并保留首次收录日期和各次观察链接；不同 URL 保留为不同内容。主看板日期筛选按最近巡查日期匹配，查看某日全部观察请进入每日存档。
- `fanka-patrol/days/YYYY-MM-DD.html`：仅展示当天巡查到的内容；同日多次发现同一原文时显示当天最新观察，附当天各次巡查入口。
- `fanka-patrol/runs/YYYY-MM-DD-NNN.html`：独立巡查存档。相对时间保留为采集当时显示值，不伪造精确发布时间。
- `fanka-patrol/exports/all.json` 与 `exports/daily/YYYY-MM-DD.json`：主看板和每日存档对应的数据导出，由原始巡查数据生成。
- `scripts/build_fanka_patrol.py` 与 `scripts/templates/fanka-patrol.html`：静态页面生成器和模板；样式、交互位于 `fanka-patrol/assets/`。
- 更新方式：加入真实的新一轮 JSON，运行 `python3 scripts/build_fanka_patrol.py`，检查页面后提交发布。生成器不采集数据，也不发送消息。
- `sentiment_category` 由已读证据人工标注：`negative`（负面）、`positive`（正面）、`mixed`（正负混合）、`neutral`（中性／咨询）、`unknown`（未判定）。缺省为未判定，不根据星级自动推断；保留 `sentiment` 说明具体倾向，赞助内容不直接算作正面。筛选选项的数量为当前页面去重总量，不随其他筛选变化。
- 不覆盖旧轮次 JSON。再次巡查需新建日期与三位序号文件，重复发现时沿用相同原文 URL；保留原始观察才能追溯旧日期内容。校验：`python3 -m unittest discover -s scripts/tests -p 'test_fanka_patrol.py'`。
- 可仅补查部分平台：当轮 `sources` 只记录实际检查的平台。主看板按平台汇总最近检查结果，逐行标明日期与轮次；每日页面仅汇总当天检查，独立存档只保留当轮结果。Google 作为发现入口，搜索摘要不单独计入评价，核实后的内容归到原文平台。
- 收录规则（Fanka、VIVAIA 共用）：品牌官方发布且没有实际读到消费者反馈的内容，只记入 `sources` 的访问说明，不加入新轮次 `records`。官方帖下实际读到的评价或咨询可收录，判断只针对消费者反馈。新增记录可用 `publisher_type`（`brand` / `consumer` / `creator` / `unknown`）与布尔值 `consumer_feedback_read` 明确来源及反馈读取情况；缺失反馈标记的官方内容默认不纳入。主看板、每日汇总、计数、筛选及对应 JSON 导出执行此规则；历史单次 HTML 与原始 JSON 保持当时观察不变。旧数据中的“品牌官方内容”“品牌官方历史内容”兼容排除，创作者合作内容仍沿用已有单独分类。
- 初版为手动巡查，未配置自动化、企微通知或后台案件处理；“建议复核”是人工编辑标记。缺失数据不是零，首轮不计算增长率或全网情绪比例。
- 用户陈述与已独立核实的事实区分；正文、评论和视频简介的读取范围分别记录；赞助内容不计为独立消费者评价。地域未知保持未知，普通账号会话不等同于免登录访问。

### VIVAIA 舆情巡查频道

`vivaia-patrol/` 与 Fanka 巡查共用展示模板和生成逻辑，数据、看板、每日存档与单次存档分别独立。入口位于早报中心的活跃频道区；与 `vivaia/` 品牌趋势日报独立。

- 主看板：`vivaia-patrol/index.html`；每日存档：`vivaia-patrol/days/YYYY-MM-DD.html`；单次存档：`vivaia-patrol/runs/YYYY-MM-DD-NNN.html`。
- 数据：`vivaia-patrol/data/YYYY-MM-DD-NNN.json`，须含 `brand: "VIVAIA"`；原始时间提示、体验日期、评价倾向及证据边界沿用 Fanka 字段。重复巡查新增文件，不覆盖旧观察。
- 生成：`python3 scripts/build_vivaia_patrol.py`。共用 `scripts/build_fanka_patrol.py` 与 `scripts/templates/fanka-patrol.html`；构建时将共用的 `fanka-patrol/assets/patrol.css`、`patrol.js` 复制至 VIVAIA 目录。共用样式或模板调整后分别运行两个构建命令。
- 首轮 2026-11-10 收录 9 条实际读取的记录：Trustpilot 6 条、Reddit 2 条、YouTube 1 条。TikTok 搜索报错，记录为未获取；没有把搜索摘要、平台 AI 总结或视频前贴广告作为用户评价。
- 本轮为近期公开网页样本，涵盖美国及其他地区，不是北美或全网全量采集。相对时间不推算为精确发布时间，用户陈述与产品事实区分，已回复不等同于已解决。
- 当前为手动巡查，不配置自动化或通知。后续先本地生成、检查，发布须遵循用户当次要求。

本地浏览器日志和页面快照位于 `.playwright-cli/`，不属于发布内容，已通过 `.gitignore` 排除。截图等正式证据仍须放在对应频道的内容目录。

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

### 所有日报共用的测试模式

正式与测试都推送到 `main`，通过目录和工作流隔离，不需要单独仓库或测试分支：

| 用途 | 文件位置 | 网页 | 通知目标 |
|---|---|---|---|
| 正式日报 | 原有各栏目目录和根目录 `latest*.json` | 原有正式地址 | 原有各栏目机器人 |
| 测试日报 | `test/<channel>/` | `/ai-news-daily/test/<channel>/` | 统一 `WECOM_WEBHOOK_TEST` |

支持的 channel 为 `tech`、`business`、`fitness`、`fanka-social`、`vivaia`。测试中心是 https://baldmuzi.github.io/ai-news-daily/test/ 。

1. 测试页面放在对应 `test/<channel>/` 下，可直接修改 `index.html` 作为固定完整预览页。首次提供的 VIVAIA 预览是正式第 0114 期的独立副本，页面注明它是样式样本，不代表新生成的日报。
2. 仅预览样式时不需要通知数据文件；没有 `latest.json` 的栏目更新只部署页面，不发消息。
3. 需要测试机器人消息时，在该目录创建 `latest.json`：保留 `edition`、`date`、`intro`、5 个 `tags`、3 个 `top3`；增加 `environment: "test"`、正确的 `channel` 和相对文件路径 `page`（默认 `index.html`）。`url` 可省略，发送脚本自动构造测试地址。
4. 如需 Fanka 延展博客，把博客也放在该测试栏目目录，使用 `blog_page`、`blog_title`、`blog_index_page` 指定相对路径；禁止填写正式博客地址。
5. `notify-test.yml` 只监听 `main` 的 `test/**`，按变更目录选择栏目，且只注入测试 Secret。所有选中栏目先统一校验，再等待完整页面和 JSON 的线上字节内容与该提交一致，最后发送。超时失败，不发送失效链接。
6. 正式 `notify.yml` 不监听 `test/**`。只推送测试目录不会触发正式通知；若同一次 push 也修改正式栏目，则相应正式通知仍会正常触发，所以测试提交只能包含测试文件。
7. 测试消息带 `【测试】`，不带正式群艾特、不回退到正式机器人。缺配置、数据标识错误、页面越界或接口错误均停止。
8. 测试自动化提示词见 `prompts/vivaia-daily-test.txt`。它使用独立副本，只写 `test/vivaia/`，只将本次测试文件推送到 `main`。
9. 修改固定页面后需提交并推送 `main` 才能在线查看更新；也可先本地预览。无需先修改或发布正式日报。Pages 仍会构建整个站点，但正式文件保持原样。

手动重发时，在 Actions 的 `Notify WeCom - test reports` 中选择测试栏目；不要运行正式通知。日志中 `target=WECOM_WEBHOOK_TEST; errcode=0` 才是发送成功。

离线验证（不会向机器人发消息）：

```sh
python3 -m unittest discover -s .github/scripts/tests -v
```

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
