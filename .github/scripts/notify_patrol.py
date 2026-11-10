"""Notify one patrol robot only after immutable published evidence matches Git."""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_fanka_patrol import aggregate, SENTIMENTS  # noqa: E402

CHANNELS = {
    'fanka': ('Fanka', 'WECOM_WEBHOOK_FANKA_PATROL'),
    'vivaia': ('VIVAIA', 'WECOM_WEBHOOK_VIVAIA_PATROL'),
}
BASE = 'https://baldmuzi.github.io/ai-news-daily/'
COVERAGE = {'complete': '计划渠道均完成读取（仍非全量）',
            'partial': '部分渠道或评论访问受限',
            'blocked': '本轮未取得可核实正文',
            'unknown': '见本次平台采集说明'}


class ConfigurationError(ValueError):
    pass


def validate_id(run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}-\d{3}', run_id):
        raise ConfigurationError('Expected run ID YYYY-MM-DD-NNN.')
    date.fromisoformat(run_id[:10])
    if run_id[-3:] == '000':
        raise ConfigurationError('Sequence must start at 001.')
    return run_id


def added_runs(channel, before, after):
    # No HEAD~1 or all-files fallback: either could replay old notifications.
    if not all(re.fullmatch(r'[0-9a-f]{40}', sha or '') and set(sha) != {'0'}
               for sha in (before, after)):
        raise ConfigurationError('Missing exact push SHAs; use a targeted manual dispatch.')
    output = subprocess.check_output(
        ['git', 'diff', '--no-renames', '--diff-filter=A', '--name-only', before, after,
         '--', f'{channel}-patrol/data/'], cwd=ROOT, text=True)
    prefix = f'{channel}-patrol/data/'
    result = []
    for name in output.splitlines():
        if name.startswith(prefix) and name.endswith('.json'):
            result.append(validate_id(name[len(prefix):-5]))
    return sorted(result)


def local_file(channel, relative):
    root = ROOT / f'{channel}-patrol'
    path = root / relative
    if root.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ConfigurationError('Patrol artifact missing or outside its channel.')
    return path


def read_run(channel, run_id):
    validate_id(run_id)
    data = json.loads(local_file(channel, f'data/{run_id}.json').read_text(encoding='utf-8'))
    brand = CHANNELS[channel][0]
    if (data.get('schema_version') != 1 or data.get('id') != run_id
            or data.get('date') != run_id[:10] or data.get('sequence') != run_id[-3:]
            or data.get('brand', 'Fanka') != brand):
        raise ConfigurationError('Patrol run identity or brand mismatch.')
    if not isinstance(data.get('sources'), list) or not isinstance(data.get('records'), list):
        raise ConfigurationError('Patrol sources and records must be lists.')
    if data.get('coverage_status', 'unknown') not in COVERAGE:
        raise ConfigurationError('Invalid coverage_status.')
    if data.get('coverage_status') == 'blocked' and data['records']:
        raise ConfigurationError('Blocked patrol cannot contain verified records.')
    ids, urls = set(), set()
    sources = {source['name'] for source in data['sources']}
    for record in data['records']:
        if (record['id'] in ids or record['url'] in urls
                or not record['url'].startswith('https://') or record['platform'] not in sources
                or record.get('sentiment_category', 'unknown') not in SENTIMENTS
                or not isinstance(record.get('priority'), bool)):
            raise ConfigurationError('Invalid or duplicate patrol record.')
        ids.add(record['id'])
        urls.add(record['url'])
    return data


def plain(value, limit=90):
    # External titles are text, never allowed to become mentions or Markdown links.
    value = re.sub(r'[\[\]<>*`#_\\]', '', str(value))
    return ' '.join(value.split())[:limit]


def prepare(channel, run_id):
    run = read_run(channel, run_id)
    records = aggregate([run])
    previous = []
    for path in sorted((ROOT / f'{channel}-patrol/data').glob('*.json')):
        if path.stem < run_id:
            previous.append(read_run(channel, path.stem))
    known = {record['url'] for record in aggregate(previous)}
    new = sum(record['url'] not in known for record in records)
    counts = Counter(record.get('sentiment_category', 'unknown') for record in records)
    focus = [record for record in records if record['priority']]
    base = f'{BASE}{channel}-patrol/'
    lines = [f'## {CHANNELS[channel][0]} 舆情巡查',
             f'{run["date"]} / {run["sequence"]} · 北京时间',
             f'覆盖：{COVERAGE[run.get("coverage_status", "unknown")]}',
             f'本轮检查 {len(run["sources"])} 个渠道；收录 {len(records)} 条观察',
             f'首次收录 {new} 条 · 复查 {len(records) - new} 条 · 建议复核 {len(focus)} 条',
             ' · '.join(f'{label} {counts[key]}' for key, label in SENTIMENTS.items()),
             '统计单位是记录卡，非独立消费者人数；首次收录不等于刚发布。']
    if not records:
        lines.append('本轮没有收录可核实记录；不代表全网没有新评价，请查看访问限制。')
    if focus:
        lines.append('\n建议复核：')
        lines.extend(f'> {plain(record["title"])}' for record in focus[:3])
    lines.extend(['', f'[本次巡查]({base}runs/{run_id}.html)',
                  f'[当天存档]({base}days/{run["date"]}.html) · [主看板]({base})'])
    content = '\n'.join(lines)
    if len(content.encode('utf-8')) > 4000:
        raise ConfigurationError('Notification too long; no message sent.')
    payload = json.dumps({'msgtype': 'markdown', 'markdown': {'content': content}},
                         ensure_ascii=False).encode('utf-8')
    # Only immutable artifacts: newer runs may legitimately replace the dashboard.
    pages = [(base + relative, local_file(channel, relative))
             for relative in (f'runs/{run_id}.html', f'data/{run_id}.json')]
    return payload, pages


def webhook_for(channel):
    # The workflow maps only secrets[matrix.secret] here; never use daily/test robots.
    webhook = os.environ.get('PATROL_WEBHOOK', '').strip()
    parsed = urlparse(webhook)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if (parsed.scheme != 'https' or parsed.netloc != 'qyapi.weixin.qq.com'
            or parsed.path != '/cgi-bin/webhook/send' or parsed.fragment
            or set(query) != {'key'} or len(query['key']) != 1 or not query['key'][0].strip()
            or ',' in webhook or any(char.isspace() for char in webhook)):
        raise ConfigurationError(f'{CHANNELS[channel][1]} missing or invalid; no message sent.')
    return webhook


def wait_for_pages(pages, timeout=600, interval=15):
    pending = {url: hashlib.sha256(path.read_bytes()).hexdigest() for url, path in pages}
    deadline = time.monotonic() + timeout
    while pending:
        for url, digest in list(pending.items()):
            request = urllib.request.Request(url + '?patrol-check=' + digest,
                                             headers={'Cache-Control': 'no-cache'})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    if response.status == 200 and hashlib.sha256(response.read()).hexdigest() == digest:
                        del pending[url]
                        print(f'Patrol artifact verified: {url}', flush=True)
            except urllib.error.HTTPError as exc:
                exc.close()
            except OSError:
                pass
        if not pending:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Published patrol artifacts do not match; no message sent.')
        print(f'Waiting for {len(pending)} patrol artifact(s)...', flush=True)
        time.sleep(min(interval, remaining))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect refused', headers, fp)


def send(channel, run_id, webhook, payload):
    request = urllib.request.Request(webhook, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            body = json.loads(response.read().decode('utf-8'))
            if response.status != 200 or not isinstance(body, dict) or body.get('errcode') != 0:
                raise ConfigurationError('WeCom rejected message; no retry or fallback.')
    except urllib.error.HTTPError as exc:
        exc.close()
        raise ConfigurationError(f'WeCom HTTP status {exc.code}; no retry or fallback.') from None
    except (OSError, ValueError) as exc:
        # Do not echo exception URLs/bodies, which can contain the webhook key.
        raise ConfigurationError(f'WeCom delivery unconfirmed ({type(exc).__name__}); no retry or fallback.') from None
    print(f'[{CHANNELS[channel][0]} 舆情巡查] run={run_id}; notification sent; '
          f'target={CHANNELS[channel][1]}; errcode=0', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', choices=CHANNELS, required=True)
    parser.add_argument('--run-id', help='Explicit existing run for preview or deliberate resend')
    parser.add_argument('--dry-run', action='store_true', help='No network, secret, or message')
    args = parser.parse_args(argv)
    try:
        runs = [validate_id(args.run_id)] if args.run_id else added_runs(
            args.channel, os.environ.get('GIT_BEFORE'), os.environ.get('GIT_AFTER'))
        if not runs:
            print(f'[{args.channel}] No added patrol runs; no message.')
            return
        if not args.dry_run:
            if os.environ.get('GITHUB_REF') != 'refs/heads/main':
                raise ConfigurationError('Sending requires refs/heads/main.')
            if os.environ.get('GITHUB_RUN_ATTEMPT', '1') != '1':
                raise ConfigurationError('Rerun blocked to avoid duplicates; inspect delivery then dispatch one run explicitly.')
            webhook = webhook_for(args.channel)
        prepared = [(run_id, *prepare(args.channel, run_id)) for run_id in runs]
        if args.dry_run:
            for _, payload, _ in prepared:
                print(json.loads(payload)['markdown']['content'])
            print('DRY RUN: no page requests or messages sent.')
            return
        wait_for_pages([page for _, _, pages in prepared for page in pages])
        for run_id, payload, _ in prepared:
            send(args.channel, run_id, webhook, payload)
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as exc:
        # ConfigurationError contains only our own redacted messages.
        message = str(exc) if isinstance(exc, ConfigurationError) else type(exc).__name__
        raise SystemExit(f'Patrol notification stopped: {message}') from None


if __name__ == '__main__':
    main()
