# Fanka / VIVAIA 每日舆情巡查配置

两份独立、可直接复制全文的任务提示词：

- [Fanka 每日舆情巡查](fanka-patrol-daily.txt)
- [VIVAIA 每日舆情巡查](vivaia-patrol-daily.txt)

这次准备了提示词和推送代码，没有创建/启用定时任务，也没有修改原有日报自动化。

## 1. 新建两个每天一次的任务

在桌面应用的定时任务中各建一项，项目都选 `ai-news-daily`，分别粘贴对应提示词全文。建议使用隔离工作树，两个时间错开，例如北京时间 Fanka 09:30、VIVAIA 10:30；时间由你选择。这两个时间只是建议，本文件不创建调度。

项目路径：`/Users/cd-20240527-002/Desktop/ai-news/ai-news-daily`。

运行环境需要 Python 3.10+、Git、现有 GitHub 推送凭证、用于核验 Actions 的 `gh` 访问权限，以及可用的网页搜索/浏览器工具。`gh` 验证状态时不要打印 token。使用本地项目的定时任务时，电脑和桌面应用需要保持运行；网页端任务不能直接操作电脑上的该目录。参见 [OpenAI 定时任务文档](https://learn.chatgpt.com/docs/automations?surface=app)。

GitHub Actions **只负责发布后的企业微信通知，不负责浏览器采集**。新增这份 workflow 不会让巡查自动开始；必须另行启用上述任务。

## 2. 新增两个 Repository Secret

进入 [仓库 Actions Secrets](https://github.com/baldmuzi/ai-news-daily/settings/secrets/actions)，点击 **New repository secret**：

| Name（必须一致） | Secret（填写完整地址） |
| --- | --- |
| `WECOM_WEBHOOK_FANKA_PATROL` | Fanka 舆情巡查群机器人的完整 Webhook URL |
| `WECOM_WEBHOOK_VIVAIA_PATROL` | VIVAIA 舆情巡查群机器人的完整 Webhook URL |

在目标企业微信群的群机器人入口添加机器人并复制其 Webhook，将完整地址直接粘贴到对应 GitHub Secret。地址格式为 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...`，不是只填写 key。

可以在同一个群创建两个机器人，也可以分群。推荐分别创建，以便消息来源清晰。不要覆盖现有 `WECOM_WEBHOOK_FITNESS`、`WECOM_WEBHOOK_FANKA_SOCIAL`、`WECOM_WEBHOOK_VIVAIA` 或 `WECOM_WEBHOOK_TEST`。无需新增 PAT、AppID、应用 Secret 或其他 mention 配置；默认不 @全体成员。

Webhook 不放进提示词、源码、网页或聊天。现有 GitHub Pages 配置保持不变。

## 3. 自动发布与通知链路

1. 桌面定时任务读取公开网页，新增本品牌 `data/YYYY-MM-DD-NNN.json`。
2. 运行生成器，更新主看板、当天页、独立巡查存档和导出数据，测试后正常推送 `main`。
3. GitHub Pages 沿用仓库已有部署方式。
4. [Notify WeCom on patrol](../.github/workflows/notify-patrol.yml) 对该次 push 的精确 before/after SHA 做差异检查，仅通知**新增的巡查 JSON 文件**。仅修改已有 JSON 不重发；仅修改样式/提示词不触发。
5. [通知脚本](../.github/scripts/notify_patrol.py) 等待本轮线上 `runs/ID.html` 和 `data/ID.json` 与本次提交的内容哈希匹配，最多约 10 分钟。HTTP 200 但内容不一致也不能发送。
6. 验证通过后只发送该品牌机器人，企业微信返回 `errcode=0` 才记录成功。缺少 Secret、部署未就绪、接口错误分别报错，不回退到旧频道机器人。

两个品牌采用独立 job；其中一个机器人缺配置不会取消另一个 job。不检查可变主看板是否仍等于旧提交，因为另一轮巡查可能已经正常更新它；通知提供已核验的本轮固定链接。

新轮次也可以是空结果或访问失败。消息会说明覆盖限制，不把“没读到”说成“没有舆情”。消息中的“首次收录/复查/倾向”按本轮记录卡计数，排除没有消费者反馈的官方内容，不能当作独立消费者人数或全网评价占比。

示意消息（数字以实际轮次为准）：

```text
Fanka 舆情巡查
日期 / 序号 · 北京时间
覆盖：部分渠道或评论访问受限
本轮检查若干渠道；收录若干条观察
首次收录 / 复查 / 建议复核
负面 / 正面 / 混合 / 中性 / 未判定
建议复核的具体事项（最多三项）
本次巡查 · 当天存档 · 主看板
```

## 4. 预览与首次验收

本地预览现有历史轮次，不需要 Secret、不发网络请求、不发群消息：

```sh
python3 .github/scripts/notify_patrol.py --channel fanka --run-id 2026-11-10-002 --dry-run
python3 .github/scripts/notify_patrol.py --channel vivaia --run-id 2026-11-10-003 --dry-run
python3 -m unittest discover -s .github/scripts/tests -p 'test_patrol_notifications.py'
```

也可以到 [巡查通知 Actions](https://github.com/baldmuzi/ai-news-daily/actions/workflows/notify-patrol.yml) 点击 **Run workflow**：分支选择 `main`，选择品牌，填写已存在的准确 `run_id`，保留 `dry_run` 勾选。只预览，不检查线上部署、Secret 是否有效，也不会发送。

添加 Secrets 后，等待下一次实际巡查发布即可自动发送。若希望用历史轮次真实试发，选择该轮次并**主动取消** `dry_run` 勾选；这会向对应正式群发送一条消息。首次真实发送后应核对群内消息和工作流日志中的品牌、run ID、`target=对应 Secret 名; errcode=0`。

本次代码验证使用 mock 网络和 dry-run，不等于已经验证真实群消息送达。企业微信接受消息也不代表群成员已阅读。

## 5. 失败与补发

- 缺 Secret：补上指定名称的 Repository Secret，发布本身不受通知失败影响。
- 部署超时：检查 Pages 是否完成，并对照本次 HTML/JSON；不通过删除原始轮次重新触发通知。
- 接口失败/网络超时：先核对群内是否已经收到。机器人 POST 不自动重试，避免不确定结果造成重复消息。
- 不使用 Actions 的 **Re-run jobs** 来补发：脚本拒绝 `GITHUB_RUN_ATTEMPT > 1` 的发送。确认未发送且希望补发后，重新 **Run workflow**，指定品牌及准确 `run_id`，取消 `dry_run`。即使同一 push 含多个轮次，也只补发失败的那一轮。
- 手动两次发起相同 `run_id` 仍可能重复发消息；当前没有跨 workflow 的持久发送账本，不保证人工重复操作的 exactly-once。
- GitHub Actions 的路径过滤本身有文件数量等平台限制；保持巡查提交范围小，若没有触发要检查 Actions，不要假设推送成功就已通知。参见 [GitHub 工作流触发文档](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)。

原始巡查 JSON 新增可选 `coverage_status`：`complete` / `partial` / `blocked`。新提示词要求填写；旧文件缺省时通知写“见本次平台采集说明”，不反推其完整性。`mode="定时巡查"` 时页面显示定时巡查，旧手动存档仍保留原来的文字。
