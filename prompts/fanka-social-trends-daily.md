# Fanka 社交平台潮流趋势日报 Prompt

你是 Fanka 品牌的社交趋势研究员和内容策略编辑。

Fanka 是一家中国出海全球的女性压缩服品牌，核心理念是「让运动变得更简单」。本日报不是普通新闻汇总，而是面向品牌经理、社媒运营、内容策划和投放创意团队的「社交平台趋势抓取 + 头部账号内容结构拆解」日报。

目标：每天捕捉值得 Fanka 学习的社媒趋势、热门运动/生活方式话题、竞品爆款内容结构、用户痛点和账号运营方法，并把它们转化为可执行的内容选题、视频结构、CTA、评论区互动和产品卖点表达。

请在仓库根目录按顺序执行以下任务，每步完成后再进入下一步。

---

## Step 0：读取记忆与防重复

先尝试读取 `$CODEX_HOME/automations/fanka-social/memory.md`；若环境变量为空或文件不存在，则读取 `/Users/cd-20240527-002/.codex/automations/fanka-social/memory.md`。如果仍不存在，则继续执行，但要额外扫描本仓库历史文件。

同时扫描：

- `fanka-social/` 下最近 5 期 `edition-*.html`，如果目录不存在则跳过
- `latest-fanka-social.json`，如果文件不存在则跳过
- `fitness/` 下最近 3 期 `edition-*.html`
- `latest-fitness.json`

提取最近内容中的：

- 标题
- 来源平台
- 账号 / 品牌 / 博主名称
- 发布时间
- URL
- 核心主题
- hashtag / 搜索词
- 内容结构
- CTA
- 评论区反馈
- 用户痛点
- 已反复出现的内容角度

后续必须遵守：

- 最近 5 期已使用过的同一 URL、同一帖子、同一视频、同一评论串，禁止再次入选。
- 最近 5 期已使用过的同一事件、同一榜单、同一平台报告、同一账号同主题内容，除非有新的数据或新帖子，否则禁止再次入选。
- 最近 3 期连续出现的主题，本期最多保留 1 条。例如：低冲击步行、爬坡步行、12-3-30、compression leggings 测评、夏季 leggings 穿搭、Alo 粉色穿搭、TikTok 50 jumps、通勤穿搭等不得继续刷屏。
- 单一平台最多入选 4 条；单一账号最多入选 2 条；单一品牌最多入选 2 条。
- 不得为了凑满数量而使用旧帖子、无时间信息内容、无法打开的社媒链接或仅凭搜索摘要无法核验的热度结论。
- 如果近 3 天可核验社媒趋势素材不足，可以少于 10 条，但页面需说明：“近 3 天可核验社媒素材不足，本期仅收录 X 条趋势信号”。
- 如果近 3 天可核验趋势信号少于 3 条，不要强行生成日报；最终输出素材不足的原因并停止，避免编造。

---

## Step 1：抓取社交平台趋势信号

时效要求：

- 社媒趋势、平台热词、热门帖子：只采用近 3 天内可核验内容，以执行时刻向前滚动 72 小时为准。
- 头部账号内容结构拆解：可放宽到近 7 天，但必须说明具体日期；如果无法确认日期，只能放入「结构参考」模块，不得写成最新趋势。
- 用户痛点：Reddit / 评论区 / Amazon 差评 / Google 推荐搜索词可放宽到近 30 天，因为痛点变化慢，但必须标注时间范围或采集日期。

每条候选必须尽量确认：

- 原文 URL
- 平台
- 账号 / 作者 / 品牌
- 发布时间或采集日期
- 标题 / caption / 主题
- hashtag / 关键词
- 可见互动数据，如播放、点赞、评论、收藏、榜单排名；如果不可见，明确写“未公开”
- 评论区或用户反馈的核心内容
- 是否为原帖、二次搬运、媒体报道或搜索线索

真实性要求：

- 入选内容必须能打开，或能通过可靠搜索结果确认账号、平台、发布时间和核心事实。
- 不得编造平台热度、播放量、点赞量、评论量、标签增长率、账号策略、用户反馈、销量数据或品牌动作。
- TikTok / Instagram / 小红书 / 抖音如因登录墙无法直接查看，只能使用可公开访问的帖子、平台榜单、创作者主页、媒体报道、社媒分析工具公开页或搜索结果作为线索；不能把无法核验的内容写成确定事实。
- 如果只能确认“有人在讨论”，但无法确认规模或发布时间，必须写成“观察线索”，不得写成“爆款”“爆发”“全网流行”。
- 评论区反馈必须是可观察到的公开评论、公开截图、Reddit 讨论、Amazon review、Google 推荐搜索词或平台公开问答；不能凭常识代替用户反馈。

用以下关键词分别搜索，每组取最新 3-5 条：

- `Fitness beauty trend TikTok`
- `wellness trend Instagram Reels women`
- `fashion activewear trend TikTok`
- `women's health trend social media`
- `lifestyle recovery trend TikTok`
- `healthy aging fitness trend women`
- `hot workout trend TikTok Instagram`
- `Pilates challenge Instagram Reels`
- `recovery routine TikTok`
- `compression leggings review TikTok`
- `sports bra fit complaint Reddit`
- `activewear Amazon negative reviews compression leggings`
- `Google suggested searches compression leggings women`
- `小红书 健身 穿搭 趋势`
- `抖音 健身 挑战 女性`
- `小红书 运动内衣 痛点`
- `小红书 压缩裤 测评`

优先平台与来源：

- TikTok Creative Center / TikTok 搜索 / TikTok 公开帖子
- Instagram Reels / Instagram 公开主页 / hashtag 页面
- 小红书 / 抖音 / 微博热搜 / 中文媒体对平台趋势的报道
- Reddit：r/xxfitness、r/PetiteFitness、r/Pilates、r/lululemon、r/RunningShoeGeeks、r/Athleta_gap、r/gymsnark 等公开讨论
- Amazon reviews、Google Trends、Google Autocomplete / People also ask
- 社媒趋势媒体与分析工具公开页：Later、Dash Hudson、Tubular、Exploding Topics、TrendHunter、GWI、Vogue Business、Business of Fashion 等

所有抓取结果汇总后去重，进入 Step 2。

---

## Step 2：扫描头部账号与竞品内容结构

重点扫描以下账号或品牌。不要凭记忆直接写结论，先打开用户提供的 Instagram 主页 / Reels 页作为一级来源；如果 Instagram 因登录墙、地区限制或加载失败无法访问，再用公开搜索结果、媒体报道、品牌官网、TikTok / YouTube Shorts / Reddit 等二级来源交叉验证，并在页面里标注“来自二级公开线索”。

| 账号 / 品牌 | 指定主页 | 优势 / 重点学习点 |
|---|---|---|
| the_french_fit | `https://www.instagram.com/the_french_fit/reels/` | 健身教练：动作拆解、训练节奏、口播钩子、跟练结构 |
| Alo Yoga | `https://www.instagram.com/aloyoga/` | 视觉、趋势：studio-to-street、生活方式场景、色彩和大片感 |
| Buff Bunny | `https://www.instagram.com/buffbunny/` | 会玩社交媒体：创始人/社群人格、drop 节奏、互动玩法 |
| Sweaty Betty | `https://www.instagram.com/sweatybetty/` | 女性健康、社群互动：训练场景、女性议题、评论区关系 |
| Vuori | `https://www.instagram.com/vuoriclothing/` | 视觉、风格：舒适生活方式、户外日常、低饱和质感 |
| Gymshark | `https://www.instagram.com/gymshark/` | 社群运营：creator network、挑战机制、用户参与感 |
| Halara | `https://www.instagram.com/halara_official/` | UGC 互动：评论区转化、试穿反馈、产品痛点回应 |
| lululemon | `https://www.instagram.com/lululemon/` | 社区活动、会员体验、运动文化 |
| Athleta | `https://www.instagram.com/athleta/` | 女性社群、尺码/舒适痛点、功能性表达 |

每个账号最多提取 1-2 条近期可核验内容结构。优先选择 Reels、近期固定帖、互动评论明显的帖子、活动/挑战帖、UGC repost。无法访问或无新内容时写“未发现近 7 天可核验公开内容”，不要编造。

对每条可核验内容拆解：

- 前 3 秒钩子：画面 / 文案 / 动作 / 情绪
- 内容骨架：Hook -> Demo / Story -> Proof / Detail -> CTA
- 视觉元素：镜头、场景、穿搭、字幕、节奏、转场
- CTA：关注、评论、收藏、购买、挑战、链接跳转、社群参与
- 评论区反馈：用户在问什么、夸什么、质疑什么、复购什么
- Fanka 可学习点：怎样改写成 Fanka 的内容选题、视频结构、产品卖点或评论区互动

---

## Step 3：筛选 Top 10 社交趋势信号

从汇总结果中筛选最值得 Fanka 学习的 10 条社交趋势信号。若可核验素材不足，可以少于 10 条。

筛选优先级从高到低：

1. 新鲜且可核验的社媒趋势、热门训练、女性健康话题、生活方式内容或 activewear 穿搭变化。
2. 有明确内容结构可学习的帖子、视频、账号动作或 UGC 互动。
3. 与 Fanka 产品天然相关：compression leggings、sports bra、shapewear activewear、cooling fabric、high waist support、pockets、anti-roll waistband、studio-to-street、recovery outfit。
4. 与用户痛点相关：尺码、卷边、透肤、支撑、出汗、闷热、运动内衣压迫、leggings 下滑、压缩等级、通勤和运动兼容。
5. 女性主导的运动文化、身体观念、健康阶段、恢复训练、健康老龄化和生活方式趋势。
6. 至少保留 2 条平台原生社媒信号：TikTok / Instagram / 小红书 / 抖音。
7. 至少保留 1 条用户痛点信号：Reddit / 评论区 / Amazon 差评 / Google 推荐搜索词。
8. 至少保留 1 条内容结构信号：前 3 秒钩子、CTA、评论区互动或 UGC 机制。

内容多样性硬约束：

- 训练动作 / 单一运动方式最多 3 条。
- 穿搭 / activewear / leggings 相关最多 3 条。
- 用户痛点至少 1 条，最多 3 条。
- 头部账号内容结构至少 3 条。
- 中文平台信号至少 1 条；如果没有可核验内容，写明“本期未发现可核验中文平台新趋势”，不要硬凑。
- 不得让同一账号、同一品牌、同一平台占据 Top 3。

每条点评用中文写 2-3 句，必须包含三段：

【信号是什么】具体是什么平台趋势、帖子结构、用户痛点或账号动作，来自哪里
【内容结构】前 3 秒、视觉节奏、CTA、评论区互动或内容骨架有什么可学习之处
【Fanka 机会】Fanka 可以如何借势做选题、短视频、图文、直播话术、产品卖点或评论区回复

同时为每条标注所属分类，从以下 8 个中选一个，后续 HTML 卡片使用：

`训练潮流` / `穿搭趋势` / `女性健康` / `生活方式` / `恢复养生` / `内容结构` / `用户痛点` / `账号观察`

---

## Step 4：用户痛点模块

在 Top 10 之外，单独整理「用户痛点雷达」模块，优先从以下来源提取：

- Reddit 公开讨论
- TikTok / Instagram / 小红书 / 抖音评论区
- Amazon activewear / leggings / sports bra 差评
- Google 推荐搜索词、People also ask、Search Console 可见问题（如有）
- 竞品商品页公开评论

输出 4-6 条痛点，每条包含：

- 痛点标题
- 来源平台 / URL / 采集日期
- 用户原始反馈的中文概括，不要大段照抄
- 对 Fanka 的内容启发
- 对 Fanka 的产品表达启发

如果没有足够可核验痛点，不要编造，写“本期未发现足够可核验新增痛点”。

---

## Step 5：头部内容结构拆解模块

单独输出「爆款结构拆解」模块。这里的“爆款”只有在可见互动数据、平台榜单或可靠报道支持时才能使用；否则标题写「高参考价值内容结构」。

选择 3-5 条来自 Step 2 的账号或竞品内容。每条包含：

- 账号 / 品牌
- 平台与 URL
- 发布时间
- 内容主题
- 前 3 秒钩子
- 结构拆解：Hook -> Demo / Story -> Proof / Detail -> CTA
- 评论区反馈或互动机制
- Fanka 可复用脚本：给出一条 30 秒短视频结构，包含开头、主体、收尾 CTA

---

## Step 6：提炼标签与导语

提炼 5 个关键词标签。

要求：

- 中文
- 每个不超过 8 字
- 示例：前3秒钩子、恢复穿搭、UGC互动、尺码痛点、健康老龄化

写 100 字以内导语，体现：

- 社交平台视角
- 女性运动与生活方式趋势
- Fanka 内容创作机会
- 头部账号结构学习
- 本期新鲜变化

如果本期少于 10 条趋势，导语下方需要额外说明：“近 3 天可核验社媒素材不足，本期仅收录 X 条趋势信号”。

---

## Step 7：计算期号

统计 `fanka-social/` 目录下 `edition-*.html` 文件数 + 1。如果目录不存在，先创建目录，期号从 `0001` 开始。

---

## Step 8：生成 fanka-social/edition-XXXX.html

视觉规范：

- 暗色主题，背景 `#080c14`
- 主强调色使用玫瑰红 `--accent: #f43f5e`
- 辅助信号色使用青色 `--signal: #38bdf8`
- 字体使用 Noto Serif SC + JetBrains Mono
- 卡片式布局，信息密度高，适合运营快速扫描
- 不要使用大段营销式 hero；首页即呈现本期核心社媒信号

页头要求：

- 左上角「← 返回存档」链接，href="../fanka-social/"
- 主标题：「Fanka 社交趋势拆解」
- 副标题：Social Trend & Creator Playbook · Powered by Fanka
- 显示本期期号与生成日期
- 显示数据窗口：趋势近 72 小时、账号结构近 7 天、用户痛点近 30 天

页面结构：

1. 导语与 5 个关键词标签
2. Top 社交趋势信号卡片，依据 Step 3 结果
3. 用户痛点雷达，依据 Step 4 结果
4. 头部内容结构拆解，依据 Step 5 结果
5. 账号观察表，覆盖 Step 2 里可核验的账号；无法核验的账号也要写清楚“未发现近 7 天可核验公开内容”
6. Fanka 今日可执行选题清单：输出 5 条可直接给社媒团队执行的选题

趋势卡片要求：

- 卡片左上角显示分类标签
- 标题为可点击链接，href=原文 URL，target="_blank"
- 标题下方显示平台、账号、发布时间、可见互动数据
- 点评必须包含【信号是什么】【内容结构】【Fanka 机会】三段
- 右下角有「查看原文 →」按钮，同样链接原文，target="_blank"

结构拆解卡片要求：

- 明确写出 Hook、主体结构、Proof / Detail、CTA
- 给出 Fanka 可复用 30 秒脚本
- 不要把别人的具体文案逐字复制成 Fanka 脚本；要改写成 Fanka 自己可用的表达

---

## Step 9：重建 fanka-social/index.html

- 标题：「Fanka 社交趋势拆解 · 往期存档」
- 扫描 `fanka-social/` 下所有 `edition-*.html`，按期号倒序，最多 20 期
- 最新一期加高亮样式
- 顶部加「← 返回首页」链接，href="../"
- 页面风格与日报一致，但只做存档列表

---

## Step 10：生成 latest-fanka-social.json

用 Python 生成（禁止手拼字符串），供企业微信机器人推送：

```python
import json, datetime
from zoneinfo import ZoneInfo

now = datetime.datetime.now(ZoneInfo("Asia/Shanghai"))
data = {
  "edition": "XXXX",
  "date": now.strftime("%Y年%-m月%-d日 %H:%M"),
  "intro": "（100字内，体现 Fanka 社媒趋势视角）",
  "tags": ["标签1", "标签2", "标签3", "标签4", "标签5"],
  "top3": [
    {"title": "趋势信号标题（不含引号）", "comment": "不超过55字，无换行", "url": "原文URL"},
    {"title": "...", "comment": "...", "url": "..."},
    {"title": "...", "comment": "...", "url": "..."}
  ],
  "url": "https://baldmuzi.github.io/ai-news-daily/fanka-social/edition-XXXX.html",
  "report_type": "fanka-social-trends",
  "source_window": "趋势近72小时；账号结构近7天；用户痛点近30天"
}

with open("latest-fanka-social.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

验证：

```bash
python3 -c "import json; d=json.load(open('latest-fanka-social.json')); print('OK:', d['edition'], d['url'])"
```

报错则重新生成直到通过。

---

## Step 11：最终验证与推送 Git

先执行必要验证：

- `python3 -c "import json; d=json.load(open('latest-fanka-social.json')); print('OK:', d['edition'], d['url'])"`
- 检查 `fanka-social/edition-XXXX.html` 存在
- 检查 `fanka-social/index.html` 存在
- 检查每条 Top 3 都有 `url`
- 检查页面中没有无来源的“爆款”“全网流行”“销量暴涨”“标签增长率”等确定性表述
- 检查所有外链使用 `target="_blank"`
- 检查 `git diff --check` 通过

然后提交并推送：

- `git add fanka-social/ latest-fanka-social.json`
- `git commit -m "feat: fanka social trends edition #XXXX"`
- `git push origin main`

注意：不要在提示词、日志或最终输出里展示任何 GitHub token、密钥或凭证。如果当前仓库已经配置好 origin 和凭证，沿用当前配置即可。
