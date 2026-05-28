# Fanka 博客页模板总结

## 结论

在 fitness 日报生成之后，额外生成一篇 Fanka 风格博客页是可行的。建议把它作为日报之后的独立步骤处理：

1. 先正常生成 `fitness/edition-XXXX.html`、`fitness/index.html` 和 `latest-fitness.json`。
2. 再从本期 Top 10 趋势里选一个最适合沉淀为长期内容的选题。
3. 参考 `fanka_html/` 里的已上线博客 HTML 和 Fanka 线上博客页，生成一篇新的 Fanka 博客 HTML。

日报负责快速扫描趋势，博客页负责把其中一个趋势转成更长期、SEO 友好、可用于 Fanka 内容运营的文章。

## 参考来源

本地模板参考：

- `2026.html`：完整压缩裤购买指南，适合参考 SEO 指南结构、FAQ、商品卡片、分享模块和完整页脚。
- `what compression level do you need.html`：完整科普型文章，适合参考表格、医学免责声明、压缩等级、商品轮播、FAQ 和最终 CTA。
- `how-to-care.html`：护理教程型文章，适合参考分步骤说明、注意事项和双图 CTA。
- `how-to-style-fanka-capri-leggings-for-any-occasion.html`：穿搭型文章，适合参考场景穿搭、造型展示、tips 卡片和 AI 图片说明。
- `how-to-pair.html`：产品搭配型文章，适合参考产品对比表和不同运动目标下的搭配逻辑，但这个文件内容不完整，不建议单独作为完整页模板。

线上参考：

- Fanka 官网：`https://www.fanka.com/`
- Fanka 博客汇总页：`https://www.fanka.com/blogs/articles`
- 生成博客时可以参考线上已发布博客页的标题结构、面包屑、作者格式、目录结构、正文语气、商品链接、FAQ 和 Keep Exploring 模块。
- 如果本地 HTML 与线上页面有差异，优先保持本地 HTML 的可复制结构，同时参考线上页面补充内容风格和内链方式。

## 商品图片和链接规则

生成博客页时，可以从 Fanka 官网商品页或商品列表页获取：

- 商品名称
- 商品详情页链接
- 商品主图或适合文章展示的商品图
- 商品系列信息，例如 Body Sculpt、PowerBand、RecoverEase
- 功能卖点，例如 compression、reversible wear、side pocket、recovery support 等

不要主动写价格，原因是价格会随地区、促销、币种和库存动态变化。文章里只写商品名称、功能、适用场景和链接即可。

如果需要商品图，优先使用 `https://cdn.shopify.com/...` 格式的图片地址。不要下载图片到仓库，直接引用线上 CDN 地址。

## 页面身份字段

每篇新博客至少要确定这些字段：

- `title`：英文 SEO 标题，例如 `How to Choose the Best Compression Leggings for Women (2026 Guide)`。
- `slug`：英文小写 URL slug，用于 `/blogs/articles/{slug}` 和本地文件名。
- `category`：通常使用 `Articles`。
- `author`：可用 `Fanka Editor`、`Fanka Designer` 或 `Fanka stylist` 加英文名。
- `publishDate`：沿用示例格式，例如 `Mar 20th, 2026`。
- `readTime`：通常为 `3 Min Read` 或 `5 Min Read`。
- `heroLink`：通常链接到相关 Fanka 商品、系列页或 `https://www.fanka.com/collections/bottoms`。
- `heroPcImage` 和 `heroMobileImage`：有合适图片时使用 Shopify CDN 图片。
- `seoDescription`：简短英文描述，用于 OG / Twitter meta。
- `primaryKeyword`：主 SEO 关键词。
- `secondaryKeywords`：3 到 6 个相关关键词。

## 固定 HTML 骨架

页面应继续使用现有单容器结构：

```html
<body>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>

  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{seoDescription}" />
  <meta name="twitter:image" content="{shareImage}" />
  <meta property="og:url" content="https://www.fanka.com/blogs/articles/{slug}" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{seoDescription}" />
  <meta property="og:image" content="{shareImage}" />

  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/Swiper/5.4.5/css/swiper.min.css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Swiper/5.4.5/js/swiper.min.js"></script>

  <style>
    /* 复制最接近的本地模板 CSS，只保留和当前页面模块相关的样式。 */
  </style>

  <div class="fanka-blog_weike">
    <!-- top_tab -->
    <!-- header_other -->
    <!-- content_body -->
    <!-- klaviyo form -->
    <!-- bottom share，可选 -->
    <!-- foot-area Keep Exploring -->
  </div>

  <script>
    /* 保留锚点平滑滚动、Swiper 初始化、移动端 Explore More 和分享逻辑。 */
  </script>
</body>
```

## 必需结构

### 1. 顶部面包屑

使用 `.top_tab`：

- `Home`
- `Wellness Hub`
- `Articles`
- 当前文章标题，链接到 `https://www.fanka.com/blogs/articles/{slug}`

移动端当前标题前保留 `<br class="show-small" />`。

### 2. 头部区域

使用 `.header_other`：

- `.header_title`：文章标题。
- `.title2 show-big`：`By {author} | {publishDate} | {readTime}`。
- `<a href="{heroLink}"><picture>...</picture></a>`：可点击头图。
- `.title2 show-small`：移动端作者和日期，放在头图后。

### 3. 正文区域

使用 `.content_body`，常用基础类如下：

- `.content-desc`：正文段落。
- `.content-big-title`：主章节标题，必须有对应 `id`。
- `.content-small-title`：小标题，常用于步骤、特征、编号说明。
- `.content-img`：单图模块。
- `.content-two-img`、`.between-two-box`、`.final-two-box`：双图或双 CTA 模块。
- `.tags-card`：目录或快速指南。
- `.btn-div`、`.goods-panel-btn`、`.m-show-btn`：CTA 按钮。
- `.understanding-table`：对比表、推荐表、等级表。
- `.faq-area`：FAQ 模块。

### 4. 目录模块

正文前部放一个 `.tags-card`：

- 科普型文章用 `Table of Contents`。
- 穿搭型文章可用 `Quick Guide`。
- 每个 `.tags-item` 必须链接到真实存在的章节 `id`。
- 可见文案保留编号，例如 `1.`、`2.`、`3.`。

### 5. 页脚模块

完整博客页通常包含：

- `<div class="klaviyo-form-XrPfme" style="margin-top: 40px"></div>`
- 可选 `.bottom-area` 分享模块，包含 Twitter、Facebook、Pinterest。
- `.foot-area` 的 `Keep Exploring`。
- 桌面端 `.foot-swiper show-big`。
- 移动端 `.foot-m show-small`。
- 移动端 `.foot-more`，点击后展开更多文章。

## 可复用文章类型

### 科普指南型

适合压缩、恢复、面料、尺码、血液循环、日常支撑、购买指南等主题。

推荐结构：

1. 用用户问题开头。
2. 放 `Table of Contents`。
3. 5 到 8 个主章节。
4. 至少一个商品推荐模块。
5. 如果主题涉及选择、等级、场景或人群，加入对比表。
6. 加一个 Fanka 立场或产品逻辑章节。
7. FAQ 3 到 5 个问题。
8. Final Thoughts 和 CTA。

参考：`2026.html`、`what compression level do you need.html`。

### 教程护理型

适合护理、清洗、穿着方法、尺码、训练前后注意事项等主题。

推荐结构：

1. 解释为什么这个问题重要。
2. 放 `Table of Contents`。
3. 用 `.content-small-title` 写多个步骤。
4. 至少一个图片或双图 CTA。
5. 加 Common Mistakes。
6. 加 A Note from Fanka。
7. 加商品或系列 CTA。

参考：`how-to-care.html`。

### 穿搭场景型

适合从日报趋势里延展出的穿搭主题，例如 capri leggings、studio-to-street、机场运动风、夏季 leggings outfit、低冲击训练穿搭等。

推荐结构：

1. 开头把趋势和 Fanka 产品联系起来。
2. 放 `Quick Guide`。
3. 按场景重复展示：场景名、Key points、Style it with、Finish with、图片。
4. 如果使用 AI 生成图片，需要加入可见说明。
5. 加 Styling Tips 或 tips cards。
6. 加产品搭配卡片。
7. 加 A Note From Fanka。
8. 加 CTA。

参考：`how-to-style-fanka-capri-leggings-for-any-occasion.html`。

### 产品搭配型

适合把趋势转成具体产品组合建议。

推荐结构：

1. 说明用户目标。
2. 产品概览表。
3. 按目标给组合建议，例如 sculpting、cardio、recovery、travel、daily support。
4. FAQ 或最终建议。
5. 商品 CTA。

参考：`how-to-pair.html`，但完整页脚和 CTA 需要参考其他完整模板。

## 常用商品和链接

这些商品在现有模板中出现过，可优先作为自动生成博客时的候选链接：

- `Body Sculpt Leggings 2.0`：`https://www.fanka.com/products/bodysculptleggings2-0`
- `PowerBand Resistance Leggings`：`https://www.fanka.com/products/powerband-resistance-leggings-reversible-wear`
- `RecoverEase Leggings`：`https://www.fanka.com/products/recoverease-leggings`
- `PowerBand Resistance Capri Leggings`：`https://www.fanka.com/products/powerband-resistance-capris-leggings-reversible-wear?variant=52061886808295`
- `Body Sculpt Bra Tank`：`https://www.fanka.com/products/body-sculpt-bra-tank?variant=50948359946471`
- `Wash Bag`：`https://www.fanka.com/products/wash-bag`
- Bottoms collection：`https://www.fanka.com/collections/bottoms`
- Fabricnology page：`https://www.fanka.com/pages/fabricnology-1`

如果执行时能从 Fanka 官网抓到更适合当日选题的商品，可以使用新的商品链接和图片，但不要写价格。

## 写作规则

- 正文使用英文，说明文档和日报仍可使用中文。
- 文章语气要像 Fanka Wellness Hub：清晰、温和、实用、面向女性、带一点产品视角。
- 不要写成新闻日报。博客要更长期、更像 SEO 文章。
- 开头先讲用户问题或趋势背景，再自然连接到 Fanka。
- 不要过度堆商品，不要每段都销售。
- 可以使用 Fanka 内链，包括商品页、系列页、Fabricnology、尺码指南、退换货、已有博客页。
- 段落要短，选择、步骤、好处、对比尽量用列表或表格。
- 涉及健康、恢复、循环、压缩等级时，不要做医疗承诺。必要时明确说明 Fanka 不是 medical-grade，医疗问题需要咨询专业人士。

## HTML 生成规则

- 优先复制最接近主题的本地 HTML 模板，不要重新设计视觉系统。
- 保留 `.fanka-blog_weike` 外层容器。
- 保留 `.show-big` 和 `.show-small` 的桌面端 / 移动端控制。
- 有桌面图和移动图时使用 `<picture>`。
- 所有目录锚点必须能跳到真实章节。
- 新页面章节 `id` 建议使用英文小写连字符，例如 `how-to-style`，不要使用空格。
- 使用商品轮播或 Keep Exploring 轮播时，保留 Swiper 5.4.5。
- 不要新增额外外部依赖。
- 输出为一个完整、自包含的 HTML 文件。

## 自动化输出要求

博客生成步骤建议输出：

- `fanka_html/{slug}.html`
- 一个简短生成摘要，包含：
  - 来源日报，例如 `fitness/edition-0010.html`
  - 选中的趋势或主题
  - 博客标题
  - slug
  - 目标关键词
  - 使用的模板类型
  - 使用的 Fanka 商品链接
  - 使用的图片来源或缺失说明

## 发布前检查

- 新文件存在于 `fanka_html/`。
- 页面 title、面包屑标题、头部标题、OG / Twitter 标题、分享标题保持一致。
- `.tags-card` 里的所有锚点都能跳到真实章节。
- 商品链接是有效的 Fanka 链接。
- 商品图片和头图使用有效的 `https://cdn.shopify.com/...` 地址，或明确标记为缺失。
- 不写商品价格。
- 桌面端和移动端都有必要内容。
- 不包含未经证实的医疗承诺。
- 不影响已有 fitness 日报页面、存档页和 JSON 结构。
