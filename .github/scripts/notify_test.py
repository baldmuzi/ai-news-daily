"""Send test/<channel>/ reports to one test robot after verifying deployed pages."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qs, quote, urlparse

from notify import build_notification_content, load_changed_files

CHANNELS = {
    'tech': 'AI 技术快讯',
    'business': 'AI 产品洞察',
    'fitness': 'Fanka 运动健康趋势',
    'fanka-social': 'Fanka 社交趋势拆解',
    'vivaia': 'VIVAIA 品牌趋势',
}
TEST_BASE_URL = 'https://baldmuzi.github.io/ai-news-daily/test/'


class TestConfigurationError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect refused', headers, fp)


def require_main():
    if os.environ.get('GITHUB_REF') != 'refs/heads/main':
        raise TestConfigurationError('Test directory notifications require refs/heads/main.')


def test_webhook():
    webhook = os.environ.get('WECOM_WEBHOOK_TEST', '').strip()
    if not webhook:
        raise TestConfigurationError('WECOM_WEBHOOK_TEST is missing; no notification sent.')
    parsed = urlparse(webhook)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if (
        parsed.scheme != 'https' or parsed.netloc != 'qyapi.weixin.qq.com'
        or parsed.path != '/cgi-bin/webhook/send' or parsed.fragment
        or set(query) != {'key'} or len(query['key']) != 1 or not query['key'][0].strip()
        or ',' in webhook or any(char.isspace() for char in webhook)
    ):
        raise TestConfigurationError('WECOM_WEBHOOK_TEST must contain one WeCom webhook URL.')
    return webhook


def selected_channels():
    require_main()
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        channel = os.environ.get('TEST_CHANNEL', '')
        if channel == 'all':
            return [key for key in CHANNELS if Path('test', key, 'latest.json').is_file()]
        if channel not in CHANNELS:
            raise TestConfigurationError('Choose one supported test channel, or all.')
        return [channel]
    changed = load_changed_files(os.environ.get('CHANGED_FILES_PATH', '/tmp/test-changed.txt'))
    selected = []
    for channel in CHANNELS:
        if any(path.startswith(f'test/{channel}/') for path in changed):
            if Path('test', channel, 'latest.json').is_file():
                selected.append(channel)
            else:
                print(f'[{channel}] preview-only changes; no test/{channel}/latest.json, no message sent.')
    return selected


def test_page(channel, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise TestConfigurationError('Test page must be a relative file path within its channel directory.')
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or '?' in relative or '#' in relative or ':' in relative:
        raise TestConfigurationError('Test page cannot point outside its channel directory.')
    root = Path('test', channel)
    path = root / parts
    if root.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise TestConfigurationError('Test page is missing or outside its channel directory.')
    url = TEST_BASE_URL + channel + '/' + quote(parts.as_posix(), safe='/')
    return url, path


def prepare_notification(channel):
    require_main()
    if channel not in CHANNELS:
        raise TestConfigurationError('Unsupported test channel.')
    webhook = test_webhook()
    json_path = Path('test', channel, 'latest.json')
    data = json.loads(json_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('environment') != 'test' or data.get('channel') != channel:
        raise TestConfigurationError(f'test/{channel}/latest.json must declare environment=test and channel={channel}.')
    if (
        not isinstance(data.get('edition'), str) or not data['edition'].isdigit()
        or not all(isinstance(data.get(key), str) for key in ('date', 'intro'))
        or not isinstance(data.get('tags'), list) or len(data['tags']) != 5
        or not all(isinstance(tag, str) for tag in data['tags'])
        or not isinstance(data.get('top3'), list) or len(data['top3']) != 3
        or not all(isinstance(item, dict) and isinstance(item.get('title'), str) for item in data['top3'])
    ):
        raise TestConfigurationError('Test JSON requires numeric edition, date, intro, five tags and three titled top3 items.')

    page_url, page_path = test_page(channel, data.get('page', 'index.html'))
    if data.get('url') not in (None, '', page_url):
        raise TestConfigurationError('Test url must match its /test/<channel>/ page; production links are refused.')
    content_data = {key: data[key] for key in ('edition', 'date', 'intro', 'tags', 'top3')}
    content_data['url'] = page_url
    pages = [(page_url, page_path), test_page(channel, 'latest.json')]
    for key in ('blog_page', 'blog_index_page'):
        if data.get(key):
            extra_url, extra_path = test_page(channel, data[key])
            pages.append((extra_url, extra_path))
            content_data['blog_url' if key == 'blog_page' else 'blog_index_url'] = extra_url
    if isinstance(data.get('blog_title'), str):
        content_data['blog_title'] = data['blog_title']
    content = build_notification_content(content_data, f'【测试】{CHANNELS[channel]}', None)
    payload = json.dumps({'msgtype': 'markdown', 'markdown': {'content': content}}).encode('utf-8')
    return webhook, payload, pages


def wait_for_test_pages(pages, timeout=480, interval=15):
    """Require actual deployed bytes to match this checkout, not just HTTP 200."""
    pending = {url: hashlib.sha256(path.read_bytes()).hexdigest() for url, path in pages}
    deadline = time.monotonic() + timeout
    while pending:
        for url, digest in list(pending.items()):
            request = urllib.request.Request(url + '?test-check=' + digest, headers={'Cache-Control': 'no-cache'})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    if response.status == 200 and hashlib.sha256(response.read()).hexdigest() == digest:
                        del pending[url]
                        print(f'Test page verified: {url}')
            except urllib.error.HTTPError as exc:
                exc.close()
            except OSError:
                pass
        if not pending:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Test pages did not match this checkout; no notification sent.')
        print(f'Waiting for {len(pending)} test page(s) to update...')
        time.sleep(min(interval, remaining))


def send_notification(channel, webhook, payload):
    request = urllib.request.Request(webhook, data=payload, headers={'Content-Type': 'application/json'})
    try:
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode('utf-8'))
            if response.status != 200 or not isinstance(body, dict) or body.get('errcode') != 0:
                sys.exit('Test notification rejected by WeCom; no fallback attempted.')
    except urllib.error.HTTPError as exc:
        exc.close()
        sys.exit(f'Test HTTP request failed (status={exc.code}); no retry or fallback.')
    except (OSError, ValueError) as exc:
        sys.exit(f'Test request failed ({type(exc).__name__}); delivery unconfirmed, no retry or fallback.')
    print(f'[【测试】{CHANNELS[channel]}] notification sent; target=WECOM_WEBHOOK_TEST; errcode=0')


def main():
    try:
        channels = selected_channels()
        if not channels:
            print('No test reports to send.')
            return
        # Validate every requested channel before performing any network calls.
        prepared = [(channel, *prepare_notification(channel)) for channel in channels]
        wait_for_test_pages([page for _, _, _, pages in prepared for page in pages])
    except TestConfigurationError as exc:
        sys.exit(str(exc))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        sys.exit(f'Test preflight/page verification failed ({type(exc).__name__}); no notification sent.')
    for channel, webhook, payload, _ in prepared:
        send_notification(channel, webhook, payload)


if __name__ == '__main__':
    main()
