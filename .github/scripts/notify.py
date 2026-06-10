import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

SOURCE_URL_KEYS = ('url', 'link', 'source_url', 'sourceUrl', 'original_url', 'originalUrl', 'href')
SOURCE_URL_RE = re.compile(r'(?:原文\s*URL|原文链接|source\s*url|source|url)\s*[:：]\s*(https?://[^\s，。；;]+)', re.I)
CATEGORY_RE = re.compile(r'(?:分类|category)\s*[:：]\s*([^。；;\n]+)', re.I)


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'a' or self._href:
            return
        href = dict(attrs).get('href', '').strip()
        if href.startswith(('http://', 'https://')):
            self._href = href
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != 'a' or not self._href:
            return
        text = normalize_text(''.join(self._text))
        if text:
            self.links.append((text, self._href))
        self._href = None
        self._text = []


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


def load_changed_files(path):
    with open(path) as f:
        return {line.strip() for line in f if line.strip()}


def should_notify(json_file, prefixes, event, changed):
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


def normalize_text(value):
    return ' '.join(str(value or '').split())


def clean_url(url):
    return str(url or '').strip().rstrip('.,，。；;')


def extract_url_from_comment(comment):
    match = SOURCE_URL_RE.search(str(comment or ''))
    return clean_url(match.group(1)) if match else ''


def extract_category(item):
    for key in ('category', 'cat', 'type'):
        value = item.get(key)
        if value:
            return normalize_text(value)
    match = CATEGORY_RE.search(str(item.get('comment', '')))
    return normalize_text(match.group(1)) if match else ''


def clean_comment(comment):
    text = str(comment or '').strip()
    text = SOURCE_URL_RE.sub('', text)
    text = CATEGORY_RE.sub('', text)
    return normalize_text(text)


def truncate_text(value, max_chars=96):
    text = normalize_text(value)
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars - 1].rstrip()}…"


def markdown_link(text, url):
    safe_text = normalize_text(text).replace('[', '\\[').replace(']', '\\]')
    safe_url = clean_url(url).replace(')', '%29')
    return f"[{safe_text}]({safe_url})"


def page_url_to_local_path(page_url, repo_root=None):
    if not page_url:
        return None
    root = Path(repo_root or os.getcwd())
    parsed = urlparse(page_url)
    raw_path = unquote(parsed.path if parsed.scheme else page_url)
    parts = [part for part in raw_path.split('/') if part]
    if parts and parts[0] == root.name:
        parts = parts[1:]
    if not parts:
        return None
    path = root.joinpath(*parts)
    return path if path.is_file() else None


def page_link_map(page_url, repo_root=None):
    path = page_url_to_local_path(page_url, repo_root)
    if not path:
        return {}
    parser = LinkExtractor()
    parser.feed(path.read_text(encoding='utf-8'))
    links = {}
    for text, href in parser.links:
        links.setdefault(normalize_text(text), href)
    return links


def source_url_for_item(item, links):
    for key in SOURCE_URL_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip().startswith(('http://', 'https://')):
            return clean_url(value)

    comment_url = extract_url_from_comment(item.get('comment', ''))
    if comment_url:
        return comment_url

    title = normalize_text(item.get('title', ''))
    if not title:
        return ''
    if title in links:
        return links[title]

    for link_title, href in links.items():
        if title in link_title or link_title in title:
            return href
    return ''


def build_top3_markdown(top3, page_url):
    links = page_link_map(page_url)
    blocks = []
    for i, item in enumerate(top3):
        title = normalize_text(item.get('title', ''))
        if not title:
            continue
        source_url = source_url_for_item(item, links) or page_url
        title_md = markdown_link(title, source_url) if source_url else title
        category = extract_category(item)
        prefix = f"#{i + 1} {category}" if category else f"#{i + 1}"
        comment = truncate_text(clean_comment(item.get('comment', '')))
        block = f"> **{prefix}** | {title_md}"
        if comment:
            block += f"\n> {comment}"
        blocks.append(block)
    return '\n\n'.join(blocks)


def build_notification_content(d, label, mention_env):
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

    top3_md = build_top3_markdown(top3, url)

    extra_links = []
    if blog_url:
        extra_links.append(markdown_link(f"📝 延展博客：{blog_title}", blog_url))
    if blog_index_url:
        extra_links.append(markdown_link("📚 Fanka 博客汇总", blog_index_url))
    extra_links_md = '\n'.join(extra_links)
    extra_links_block = f"\n\n{extra_links_md}" if extra_links_md else ''

    mentions = build_mention_str(mention_env)
    msg = os.environ.get(mention_env.replace('MENTION', 'MENTION_MSG'), '').strip()
    mention_line = f"\n{mentions} {msg}".rstrip() if mentions else ''

    title = f"{label} #{edition}".strip()
    return (
        f"# {title} 🤖\n"
        f"{date} · 北京时间\n\n"
        f"{intro}\n\n"
        f"**关键词：** {tags}\n\n"
        f"**Top 3 速览：**\n{top3_md}\n\n"
        f"{markdown_link('📖 阅读完整版', url)}"
        f"{extra_links_block}"
        f"{mention_line}"
    )


def post_wecom(webhook_env_val, json_path, label, mention_env):
    if not webhook_env_val:
        print(f"[{label}] webhook not set, skip")
        return
    if not os.path.exists(json_path):
        print(f"[{label}] {json_path} not found, skip")
        return

    with open(json_path, encoding='utf-8') as f:
        d = json.load(f)

    url = d.get('url', '')
    blog = d.get('blog') or {}
    blog_url = blog.get('url') or d.get('blog_url', '')
    blog_index_url = d.get('blog_index_url', '')

    wait_for_page(url)
    if blog_url:
        wait_for_page(blog_url)
    if blog_index_url:
        wait_for_page(blog_index_url)

    content = build_notification_content(d, label, mention_env)

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


def main():
    event = os.environ.get('GITHUB_EVENT_NAME', 'push')
    changed_file = os.environ.get('CHANGED_FILES_PATH', '/tmp/changed.txt')
    changed = load_changed_files(changed_file)

    print(f"event={event}  changed={changed}")

    if should_notify('latest.json', 'editions/', event, changed):
        post_wecom(os.environ.get('WECOM_WEBHOOK_TECH', ''), 'latest.json', 'AI 技术快讯', 'WECOM_MENTION_TECH')

    if should_notify('latest-business.json', 'business/', event, changed):
        post_wecom(os.environ.get('WECOM_WEBHOOK_BUSINESS', ''), 'latest-business.json', 'AI 产品洞察', 'WECOM_MENTION_BUSINESS')

    if should_notify('latest-fitness.json', ('fitness/', 'fanka_html/'), event, changed):
        post_wecom(os.environ.get('WECOM_WEBHOOK_FITNESS', ''), 'latest-fitness.json', 'Fanka 运动健康趋势', 'WECOM_MENTION_FITNESS')

    if should_notify('latest-vivaia.json', 'vivaia/', event, changed):
        post_wecom(os.environ.get('WECOM_WEBHOOK_VIVAIA', ''), 'latest-vivaia.json', 'VIVAIA 品牌趋势', 'WECOM_MENTION_VIVAIA')


if __name__ == '__main__':
    main()
