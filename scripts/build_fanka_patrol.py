#!/usr/bin/env python3
"""Build the Fanka patrol dashboard and dated snapshots; no network or sends."""
import json
import hashlib
import shutil
from collections import defaultdict
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
CHANNEL = ROOT / 'fanka-patrol'
SENTIMENTS = {'negative': '负面评价', 'positive': '正面评价', 'mixed': '正负混合',
              'neutral': '中性／咨询', 'unknown': '未判定'}


def e(value):
    return escape(str(value), quote=True)


def render_record(r, prefix):
    category = r.get('sentiment_category', 'unknown')
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
    observations = r['_observations']
    history = ' · '.join(f'<a href="{prefix}runs/{e(o["run_id"])}.html#{e(o["record_id"])}">{e(o["date"])} / {e(o["sequence"])}</a>' for o in reversed(observations))
    return f'''<article class="record" id="{e(r['id'])}" data-date="{e(r['_last_seen'])}" data-platform="{e(r['platform'])}" data-kind="{e(r['kind'])}" data-sentiment="{e(category)}" data-priority="{str(r['priority']).lower()}" data-search="{e(search)}">
      <div class="record-meta"><span class="platform">{e(r['platform'])}</span><span>{e(r['kind'])}{rating}</span>{priority}</div>
      <h3>{e(r['title'])}</h3>
      <div class="observation-time">首次收录 {e(r['_first_seen'])} · 最近巡查 {e(r['_last_seen'])}</div>
      <div class="record-time"><span>原文发布时间：{e(r['published_label'])}（{e(r['_last_seen'])} 巡查时）</span>{experience}<span>地区：{e(r['region'])}</span></div>
      <p class="summary">{e(r['summary'])}</p>
      <div class="tags"><span class="sentiment-category">{SENTIMENTS[category]}</span>{tags}<span class="sentiment">{e(r['sentiment'])}</span></div>
      <details><summary>证据范围与建议</summary><div class="evidence"><p><strong>已核实范围</strong>{e(r['evidence'])}</p><p><strong>建议下一步</strong>{e(r['action'])}</p>{metrics}<p><strong>巡查记录</strong>{history}</p></div></details>
      <a class="source-link" href="{e(r['url'])}" target="_blank" rel="noopener noreferrer">查看原文 <span aria-hidden="true">↗</span></a>
    </article>'''


def aggregate(runs):
    """One source URL per card; retain earliest anchor and all observations."""
    merged = {}
    used_ids = set()
    for run in sorted(runs, key=lambda d: d['id']):
        for record in run['records']:
            key = record['url']
            previous = merged.get(key)
            if previous:
                anchor = previous['id']
                first_seen = previous['_first_seen']
                observations = previous['_observations'][:]
            else:
                anchor = record['id']
                if anchor in used_ids:
                    anchor += '-' + hashlib.sha256(key.encode()).hexdigest()[:12]
                used_ids.add(anchor)
                first_seen = run['date']
                observations = []
            observations.append({'date': run['date'], 'run_id': run['id'],
                                 'sequence': run['sequence'], 'record_id': record['id']})
            merged[key] = dict(record, id=anchor, _first_seen=first_seen,
                               _last_seen=run['date'], _last_run=run['id'],
                               _observations=observations)
    # Stable source order inside the same run; never infer exact publish times.
    return sorted(merged.values(), key=lambda r: r['_last_run'], reverse=True)


def aggregate_sources(runs):
    """Keep each platform's latest actual check, including partial patrols."""
    sources = {}
    for run in sorted(runs, key=lambda d: d['id']):
        for source in run['sources']:
            sources[source['name']] = dict(source, _run_id=run['id'],
                                           _date=run['date'], _sequence=run['sequence'])
    return list(sources.values())


def render(data, runs, mode='main', selected_runs=None, brand='Fanka'):
    snapshot = mode == 'run'
    prefix = '' if mode == 'main' else '../'
    selected_runs = selected_runs or ([data] if snapshot else runs)
    records = aggregate(selected_runs)
    day = mode == 'day'
    scope = '全部巡查' if mode == 'main' else ('当天巡查' if day else '本次巡查')
    focus = [r for r in records if r['priority']]
    sources = aggregate_sources(selected_runs)
    kinds = sorted({r['kind'] for r in records})
    platforms = sorted({r['platform'] for r in records})
    attention = ''.join(f'''<a class="focus-item" href="#{e(r['id'])}" data-reveal="{e(r['id'])}">
      <span class="focus-number">0{i}</span><div><span class="focus-meta">{e(r['platform'])} · 建议复核</span><h3>{e(r['title'])}</h3><p>{e(r['action'])}</p></div><span class="focus-arrow" aria-hidden="true">↗</span></a>'''
      for i, r in enumerate(focus, 1))
    def source_time(source):
        if snapshot:
            return ''
        return f'<small>最近检查：<a href="{prefix}runs/{e(source["_run_id"])}.html#coverage">{e(source["_date"])} / {e(source["_sequence"])}</a></small>'
    rows = ''.join(f'''<tr><th scope="row"><a href="{e(s['url'])}" target="_blank" rel="noopener noreferrer">{e(s['name'])} ↗</a><small>{e(s['access'])}</small>{source_time(s)}</th><td><strong>{e(s['status'])}</strong><p>{e(s['detail'])}</p></td><td>{e(s['sorting'])}</td><td>{e(s['limitation'])}</td></tr>''' for s in sources)
    dates = sorted({d['date'] for d in runs}, reverse=True)
    archive = ''.join(f'<a class="archive-link" href="{prefix}days/{e(date)}.html"><span>{e(date)} · 当天巡查</span><span>{sum(d["date"] == date for d in runs)} 次巡查 ↗</span></a>' for date in dates)
    if snapshot:
        notice = f'这是 {e(data["date"])} 第 {e(data["sequence"])} 次巡查的独立存档。<a href="../days/{e(data["date"])}.html">查看当天巡查</a> · <a href="../index.html">返回主看板</a>'
    elif day:
        notice = f'仅展示 {e(data["date"])} 当天巡查收录的内容。<a href="../index.html">返回全部巡查主看板</a>'
    else:
        notice = '主看板汇总全部巡查；同一原文合并展示最新观察，历史观察保留在存档中。当前为手动巡查。'
    groups = defaultdict(list)
    for record in records:
        groups[record['_last_seen']].append(record)
    rendered_records = ''.join(f'<section class="date-group" data-date="{e(date)}" aria-label="{e(date)} 巡查记录"><div class="date-heading"><h3>{e(date)}</h3><a href="{prefix}days/{e(date)}.html">查看当天巡查 ↗</a></div>' + '\n'.join(render_record(r, prefix) for r in rows) + '</section>' for date, rows in groups.items())
    run_links = ''.join(f'<a class="archive-link" href="{prefix}runs/{e(d["id"])}.html"><span>第 {e(d["sequence"])} 次巡查</span><span>{len(d["records"])} 条观察 ↗</span></a>' for d in selected_runs)
    if day or snapshot:
        archive = run_links
    download = 'exports/all.json' if mode == 'main' else (f'exports/daily/{data["date"]}.json' if day else f'data/{data["id"]}.json')
    return Template((ROOT / 'scripts/templates/fanka-patrol.html').read_text()).substitute(
        brand=e(brand), prefix=prefix, home='../' if mode == 'main' else '../../', date=e(data['date']),
        sequence=e(data['sequence']), notice=notice, scope=scope,
        scope_description='全部巡查记录，按最近巡查日期倒序' if mode == 'main' else ('仅展示当天巡查到的内容' if day else '保留本次巡查当时的观察'),
        sentiment_options=''.join(f'<option value="{key}">{label}（{sum(r.get("sentiment_category", "unknown") == key for r in records)}）</option>' for key, label in SENTIMENTS.items()),
        date_options=''.join(f'<option>{e(date)}</option>' for date in groups),
        issue_label='最近巡查' if mode == 'main' else '巡查记录',
        records_title='全部记录' if mode == 'main' else ('当天记录' if day else '本次记录'),
        archive_title='每日巡查存档' if mode == 'main' else ('当天各次巡查' if day else '本次巡查存档'),
        coverage_note=f'{data["date"]} / {data["sequence"]} 的访问结果；历史情况见各次存档' if snapshot else '各平台最近一次巡查结果；检查日期与轮次见表内',
        coverage_caption='最近一次巡查的平台访问结果' if snapshot else '各平台最近一次实际检查结果',
        source_label='最近一次检查平台' if snapshot else '已巡查平台',
        count=f'{len(records):02}', attention_count=f'{len(focus):02}', source_count=f'{len(sources):02}',
        attention=attention, records=rendered_records, source_rows=rows,
        platform_options=''.join(f'<option>{e(p)}</option>' for p in platforms),
        kind_options=''.join(f'<option>{e(k)}</option>' for k in kinds), archive=archive,
        run_json=f'{prefix}{download}',
        snapshot_url=f'{prefix}runs/{e(data["id"])}.html',
        description=f'{len(selected_runs)} 次巡查 · {len({run["date"] for run in selected_runs})} 个日期' if mode == 'main' else scope,
    )


def main(channel=None, brand='Fanka'):
    channel = Path(channel) if channel is not None else CHANNEL
    runs = [json.loads(p.read_text()) for p in sorted((channel / 'data').glob('*.json'), reverse=True)]
    if not runs:
        raise ValueError('No patrol data')
    for d in runs:
        assert d['schema_version'] == 1 and d['id'] == d['date'] + '-' + d['sequence']
        assert d.get('brand', brand) == brand, 'Patrol data belongs to a different brand'
        ids = [r['id'] for r in d['records']]
        assert len(ids) == len(set(ids)), 'Duplicate record IDs'
        urls = [r['url'] for r in d['records']]
        assert len(urls) == len(set(urls)), 'Duplicate source URLs'
        assert all(r.get('sentiment_category', 'unknown') in SENTIMENTS for r in d['records']), 'Invalid sentiment category'
        assert all(url.startswith('https://') for url in urls)
        assert all(r['platform'] in {s['name'] for s in d['sources']} for r in d['records'])
    # Both channels use the same interaction and visual assets.
    assets = ROOT / 'fanka-patrol/assets'
    if channel.resolve() != assets.parent.resolve():
        (channel / 'assets').mkdir(exist_ok=True)
        for filename in ('patrol.css', 'patrol.js'):
            shutil.copyfile(assets / filename, channel / 'assets' / filename)
    (channel / 'runs').mkdir(exist_ok=True)
    for d in runs:
        # An archive only lists runs that existed at that snapshot.
        history = [run for run in runs if run['id'] <= d['id']]
        (channel / 'runs' / f'{d["id"]}.html').write_text(render(d, history, mode='run', brand=brand))
    (channel / 'days').mkdir(exist_ok=True)
    (channel / 'exports/daily').mkdir(parents=True, exist_ok=True)
    for date in sorted({d['date'] for d in runs}):
        daily_runs = [d for d in runs if d['date'] == date]
        (channel / 'days' / f'{date}.html').write_text(render(daily_runs[0], daily_runs, mode='day', brand=brand))
        (channel / 'exports/daily' / f'{date}.json').write_text(json.dumps({'brand': brand, 'date': date, 'runs': [d['id'] for d in daily_runs], 'records': aggregate(daily_runs)}, ensure_ascii=False, indent=2) + '\n')
    (channel / 'exports/all.json').write_text(json.dumps({'brand': brand, 'updated_date': runs[0]['date'], 'runs': [d['id'] for d in runs], 'records': aggregate(runs)}, ensure_ascii=False, indent=2) + '\n')
    (channel / 'index.html').write_text(render(runs[0], runs, brand=brand))
    print(f'Built dashboard + {len(runs)} snapshot(s); {len(aggregate(runs))} unique records')


if __name__ == '__main__':
    main()
