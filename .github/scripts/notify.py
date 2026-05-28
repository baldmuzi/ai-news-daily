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


def should_notify(json_file, prefixes):
    if event == 'workflow_dispatch':
        return os.path.exists(json_file)
    if isinstance(prefixes, str):
        prefixes = (prefixes,)
    return json_file in changed or any(
        any(f.startswith(prefix) for prefix in prefixes)
        for f in changed
    )


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
    blog = d.get('blog') or {}
    blog_url = blog.get('url') or d.get('blog_url', '')
    blog_title = blog.get('title') or d.get('blog_title') or '本期延展博客'
    blog_index_url = d.get('blog_index_url', '')

    wait_for_page(url)
    if blog_url:
        wait_for_page(blog_url)
    if blog_index_url:
        wait_for_page(blog_index_url)

    top3_md = '\n'.join(
        f"> **#{i+1} {it.get('title', '')}**\n> {it.get('comment', '')[:80]}"
        for i, it in enumerate(top3)
    )

    extra_links = []
    if blog_url:
        extra_links.append(f"[📝 延展博客：{blog_title}]({blog_url})")
    if blog_index_url:
        extra_links.append(f"[📚 Fanka 博客汇总]({blog_index_url})")
    extra_links_md = '\n'.join(extra_links)
    extra_links_block = f"\n\n{extra_links_md}" if extra_links_md else ''

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
        f"{extra_links_block}"
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
        last_err = None
        for attempt in range(1, 4):  # up to 3 attempts
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = json.loads(resp.read().decode('utf-8'))
                    if body.get('errcode') != 0:
                        sys.exit(f"WeCom error: {body}")
                    print(f"[{label}] notification sent ✓ ({webhook[-8:]}…)")
                    last_err = None
                    break
            except Exception as e:
                last_err = e
                print(f"[{label}] attempt {attempt} failed: {e}, retrying in 10s…")
                time.sleep(10)
        if last_err:
            sys.exit(f"[{label}] all attempts failed: {last_err}")


if should_notify('latest.json', 'editions/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_TECH', ''), 'latest.json', 'AI 技术快讯', 'WECOM_MENTION_TECH')

if should_notify('latest-business.json', 'business/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_BUSINESS', ''), 'latest-business.json', 'AI 产品洞察', 'WECOM_MENTION_BUSINESS')

if should_notify('latest-fitness.json', ('fitness/', 'fanka_html/')):
    post_wecom(os.environ.get('WECOM_WEBHOOK_FITNESS', ''), 'latest-fitness.json', 'Fanka 运动健康趋势', 'WECOM_MENTION_FITNESS')

if should_notify('latest-vivaia.json', 'vivaia/'):
    post_wecom(os.environ.get('WECOM_WEBHOOK_VIVAIA', ''), 'latest-vivaia.json', 'VIVAIA 品牌趋势', 'WECOM_MENTION_VIVAIA')
