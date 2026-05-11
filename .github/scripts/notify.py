import json
import os
import sys
import time
import urllib.request
import urllib.error

event = os.environ.get('GITHUB_EVENT_NAME', 'push')
changed_file = os.environ.get('CHANGED_FILES_PATH', '/tmp/changed.txt')

with open(changed_file) as f:
    changed = {line.strip() for line in f if line.strip()}

print(f"event={event}  changed={changed}")


def wait_for_page(url, timeout=480, interval=20):
    """Poll url every interval seconds until HTTP 200 or timeout."""
    if not url:
        return
    print(f"Waiting for GitHub Pages: {url}")
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    print(f"Page ready after {int(time.time() - start)}s ✓")
                    return
        except urllib.error.HTTPError as e:
            elapsed = int(time.time() - start)
            print(f"  {e.code} — not ready yet ({elapsed}s elapsed)")
        except Exception as e:
            print(f"  request error: {e}")
        time.sleep(interval)
    print(f"Timeout after {timeout}s, sending notification anyway")


def should_notify(json_file, prefix):
    if event == 'workflow_dispatch':
        return os.path.exists(json_file)
    return json_file in changed or any(f.startswith(prefix) for f in changed)


def build_mention_str(mention_env):
    raw = os.environ.get(mention_env, '').strip()
    if not raw:
        return ''
    return ''.join(f'<@{uid.strip()}>' for uid in raw.split(',') if uid.strip())


def post_wecom(webhook_env_val, json_path, label, mention_env):
    if not webhook_env_val:
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

    wait_for_page(url)

    top3_md = '\n'.join(
        f"> **#{i+1} {it.get('title', '')}**\n> {it.get('comment', '')[:80]}"
        for i, it in enumerate(top3)
    )

    mentions = build_mention_str(mention_env)
    msg = os.environ.get(mention_env.replace('MENTION', 'MENTION_MSG'), '').strip()
    mention_line = f"\n{mentions} {msg}".rstrip() if mentions else ''

    content = (
        f"**{label} #{edition}** 🤖\n"
        f"{date} · 北京时间\n\n"
        f"{intro}\n\n"
        f"**关键词：** {tags}\n\n"
        f"**Top 3 速览：**\n{top3_md}\n\n"
        f"[📖 阅读完整版]({url})"
        f"{mention_line}"
    )

    payload = json.dumps({
        'msgtype': 'markdown',
        'markdown': {'content': content}
    }).encode('utf-8')

    webhooks = [w.strip() for w in webhook_env_val.split(',') if w.strip()]
    for webhook in webhooks:
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode('utf-8'))
            if body.get('errcode') != 0:
                sys.exit(f"WeCom error: {body}")
            print(f"[{label}] notification sent ✓ ({webhook[-8:]}…)")


if should_notify('latest.json', 'editions/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_TECH', ''), 'latest.json', 'AI 技术快讯', 'WECOM_MENTION_TECH')

if should_notify('latest-business.json', 'business/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_BUSINESS', ''), 'latest-business.json', 'AI 产品洞察', 'WECOM_MENTION_BUSINESS')

if should_notify('latest-fitness.json', 'fitness/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_FITNESS', ''), 'latest-fitness.json', 'Fanka 运动健康趋势', 'WECOM_MENTION_FITNESS')
