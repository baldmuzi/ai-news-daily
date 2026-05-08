import json
import os
import sys
import urllib.request

event = os.environ.get('GITHUB_EVENT_NAME', 'push')
changed_file = os.environ.get('CHANGED_FILES_PATH', '/tmp/changed.txt')

with open(changed_file) as f:
    changed = {line.strip() for line in f if line.strip()}

print(f"event={event}  changed={changed}")


def should_notify(json_file, prefix):
    if event == 'workflow_dispatch':
        return os.path.exists(json_file)
    return json_file in changed or any(f.startswith(prefix) for f in changed)


def post_wecom(webhook, json_path, label):
    if not webhook:
        print(f"[{label}] webhook not set, skip")
        return
    if not os.path.exists(json_path):
        print(f"[{label}] {json_path} not found, skip")
        return

    with open(json_path, encoding='utf-8') as f:
        d = json.load(f)

    edition = d.get('edition', '')
    date = d.get('date', '')
    intro = d.get('intro', '')
    tags = ' · '.join(d.get('tags', []))
    url = d.get('url', '')
    top3 = d.get('top3', [])

    top3_md = '\n'.join(
        f"> **#{i+1} {it.get('title', '')}**\n> {it.get('comment', '')[:80]}"
        for i, it in enumerate(top3)
    )

    content = (
        f"**{label} #{edition}** 🤖\n"
        f"{date} · 北京时间\n\n"
        f"{intro}\n\n"
        f"**关键词：** {tags}\n\n"
        f"**Top 3 速览：**\n{top3_md}\n\n"
        f"[📖 阅读完整版]({url})"
    )

    payload = json.dumps({
        'msgtype': 'markdown',
        'markdown': {'content': content}
    }).encode('utf-8')

    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode('utf-8'))
        if body.get('errcode') != 0:
            sys.exit(f"WeCom error: {body}")
        print(f"[{label}] OK")


if should_notify('latest.json', 'editions/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_TECH', ''), 'latest.json', 'AI 技术快讯')

if should_notify('latest-business.json', 'business/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_BUSINESS', ''), 'latest-business.json', 'AI 产品洞察')
