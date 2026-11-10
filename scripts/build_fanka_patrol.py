#!/usr/bin/env python3
"""Build the Fanka patrol dashboard and dated snapshots; no network or sends."""
import json
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
CHANNEL = ROOT / 'fanka-patrol'


def e(value):
    return escape(str(value), quote=True)


def render_record(r):
    tags = ''.join(f'<span class="tag">{e(t)}</span>' for t in r['topics'])
    rating = f' · {r["rating"]} / 5 星' if r['rating'] is not None else ''
    metric_labels = {'views': '观看', 'likes': '赞', 'saves': '收藏', 'comments': '评论'}
    metrics = ''
    if r['metrics']:
        values = ' · '.join(f'{v:,} {metric_labels[k]}' for k, v in r['metrics'].items())
        metrics = f'<p class="metrics-note">访问时快照：{values}；不随页面打开实时更新。</p>'
    experience = f'<span>体验日期：{e(r["experience_date"])}</span>' if r['experience_date'] else ''
    search = ' '.join([r['title'], r['summary'], r['platform'], r['kind'], *r['topics']])
    priority = '<span class="priority">建议复核</span>' if r['priority'] else ''
    return f'''<article class="record" id="{e(r['id'])}" data-platform="{e(r['platform'])}" data-kind="{e(r['kind'])}" data-priority="{str(r['priority']).lower()}" data-search="{e(search)}">
      <div class="record-meta"><span class="platform">{e(r['platform'])}</span><span>{e(r['kind'])}{rating}</span>{priority}</div>
      <h3>{e(r['title'])}</h3>
      <div class="record-time"><span>{e(r['published_label'])}</span>{experience}<span>地区：{e(r['region'])}</span></div>
      <p class="summary">{e(r['summary'])}</p>
      <div class="tags">{tags}<span class="sentiment">{e(r['sentiment'])}</span></div>
      <details><summary>证据范围与建议</summary><div class="evidence"><p><strong>已核实范围</strong>{e(r['evidence'])}</p><p><strong>建议下一步</strong>{e(r['action'])}</p>{metrics}</div></details>
      <a class="source-link" href="{e(r['url'])}" target="_blank" rel="noopener noreferrer">查看原文 <span aria-hidden="true">↗</span></a>
    </article>'''


def render(data, runs, snapshot=False):
    prefix = '../' if snapshot else ''
    records = data['records']
    focus = [r for r in records if r['priority']]
    sources = data['sources']
    kinds = sorted({r['kind'] for r in records})
    platforms = sorted({r['platform'] for r in records})
    attention = ''.join(f'''<a class="focus-item" href="#{e(r['id'])}" data-reveal="{e(r['id'])}">
      <span class="focus-number">0{i}</span><div><span class="focus-meta">{e(r['platform'])} · 建议复核</span><h3>{e(r['title'])}</h3><p>{e(r['action'])}</p></div><span class="focus-arrow" aria-hidden="true">↗</span></a>'''
      for i, r in enumerate(focus, 1))
    rows = ''.join(f'''<tr><th scope="row"><a href="{e(s['url'])}" target="_blank" rel="noopener noreferrer">{e(s['name'])} ↗</a><small>{e(s['access'])}</small></th><td><strong>{e(s['status'])}</strong><p>{e(s['detail'])}</p></td><td>{e(s['sorting'])}</td><td>{e(s['limitation'])}</td></tr>''' for s in sources)
    archive = ''.join(f'<a class="archive-link" href="{prefix}runs/{e(d["id"])}.html"><span>{e(d["date"])} · 第 {e(d["sequence"])} 次</span><span>{len(d["records"])} 条记录 ↗</span></a>' for d in runs)
    notice = ('这是第 ' + data['sequence'] + ' 次巡查的存档。<a href="../index.html">返回最新看板</a>') if snapshot else '本页展示最近一次巡查快照；当前未启用定时采集。'
    return Template((ROOT / 'scripts/templates/fanka-patrol.html').read_text()).substitute(
        prefix=prefix, home='../../' if snapshot else '../', date=e(data['date']),
        sequence=e(data['sequence']), notice=notice,
        count=f'{len(records):02}', attention_count=f'{len(focus):02}', source_count=f'{len(sources):02}',
        attention=attention, records='\n'.join(render_record(r) for r in records), source_rows=rows,
        platform_options=''.join(f'<option>{e(p)}</option>' for p in platforms),
        kind_options=''.join(f'<option>{e(k)}</option>' for k in kinds), archive=archive,
        run_json=f'{prefix}data/{e(data["id"])}.json',
        snapshot_url=f'{prefix}runs/{e(data["id"])}.html',
        description='首次巡查基线' if data['baseline'] else '巡查记录',
    )


def main():
    runs = [json.loads(p.read_text()) for p in sorted((CHANNEL / 'data').glob('*.json'), reverse=True)]
    if not runs:
        raise ValueError('No patrol data')
    for d in runs:
        assert d['schema_version'] == 1 and d['id'] == d['date'] + '-' + d['sequence']
        ids = [r['id'] for r in d['records']]
        assert len(ids) == len(set(ids)), 'Duplicate record IDs'
        urls = [r['url'] for r in d['records']]
        assert len(urls) == len(set(urls)), 'Duplicate source URLs'
        assert all(url.startswith('https://') for url in urls)
        assert all(r['platform'] in {s['name'] for s in d['sources']} for r in d['records'])
    (CHANNEL / 'runs').mkdir(exist_ok=True)
    for d in runs:
        # An archive only lists runs that existed at that snapshot.
        history = [run for run in runs if run['id'] <= d['id']]
        (CHANNEL / 'runs' / f'{d["id"]}.html').write_text(render(d, history, snapshot=True))
    (CHANNEL / 'index.html').write_text(render(runs[0], runs))
    print(f'Built dashboard + {len(runs)} snapshot(s); {len(runs[0]["records"])} current records')


if __name__ == '__main__':
    main()
