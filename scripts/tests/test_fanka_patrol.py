"""Cross-day patrol behavior; fixtures stay in temporary directories only."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'patrol', Path(__file__).resolve().parents[1] / 'build_fanka_patrol.py')
patrol = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patrol)


class PatrolHistoryTests(unittest.TestCase):
    def setUp(self):
        self.first = json.loads((patrol.CHANNEL / 'data/2026-11-10-001.json').read_text())
        self.next = copy.deepcopy(self.first)
        self.next.update(date='2026-11-11', id='2026-11-11-001')
        self.next['records'] = self.next['records'][:1]
        self.next['records'][0].update(id='revisited', summary='Updated observation fixture')

    def test_revisit_keeps_anchor_history_and_old_records(self):
        original = copy.deepcopy(self.first)
        records = patrol.aggregate([self.next, self.first])
        self.assertEqual(len(records), 6)
        revisited = records[0]
        self.assertEqual(revisited['id'], 'tp-delivery')
        self.assertEqual(revisited['_first_seen'], '2026-11-10')
        self.assertEqual(revisited['_last_seen'], '2026-11-11')
        self.assertEqual(revisited['summary'], 'Updated observation fixture')
        self.assertEqual([o['record_id'] for o in revisited['_observations']],
                         ['tp-delivery', 'revisited'])
        self.assertEqual(self.first, original)

    def test_different_urls_with_same_id_remain_separate(self):
        self.next['records'][0].update(id='tp-delivery', url='https://example.com/new-review')
        records = patrol.aggregate([self.next, self.first])
        self.assertEqual(len(records), 7)
        self.assertEqual(len({r['id'] for r in records}), 7)
        self.assertEqual(records[0]['url'], 'https://example.com/new-review')

    def test_build_daily_isolation_and_snapshot_preservation(self):
        later = copy.deepcopy(self.next)
        later.update(sequence='002', id='2026-11-11-002')
        later['records'][0]['summary'] = 'Later same-day observation fixture'
        with tempfile.TemporaryDirectory() as directory:
            channel = Path(directory)
            (channel / 'data').mkdir()
            with patch.object(patrol, 'CHANNEL', channel):
                (channel / 'data' / f'{self.first["id"]}.json').write_text(json.dumps(self.first))
                patrol.main()
                old_snapshot = (channel / 'runs/2026-11-10-001.html').read_text()
                for run in [self.next, later]:
                    (channel / 'data' / f'{run["id"]}.json').write_text(json.dumps(run))
                patrol.main()
            main = json.loads((channel / 'exports/all.json').read_text())
            day = json.loads((channel / 'exports/daily/2026-11-11.json').read_text())
            old_day = json.loads((channel / 'exports/daily/2026-11-10.json').read_text())
            self.assertEqual(len(main['records']), 6)
            self.assertEqual(len(old_day['records']), 6)
            self.assertEqual(len(day['records']), 1)
            self.assertEqual(day['records'][0]['summary'], 'Later same-day observation fixture')
            self.assertEqual(len(day['records'][0]['_observations']), 2)
            self.assertEqual((channel / 'runs/2026-11-10-001.html').read_text(), old_snapshot)
            daily_page = (channel / 'days/2026-11-11.html').read_text()
            self.assertIn('href="../../"', daily_page)
            self.assertNotIn('tp-positive', daily_page)
            self.assertIn('../runs/2026-11-11-001.html', daily_page)
            self.assertIn('../runs/2026-11-11-002.html', daily_page)
            index = (channel / 'index.html').read_text()
            self.assertLess(index.index('class="date-group" data-date="2026-11-11"'),
                            index.index('class="date-group" data-date="2026-11-10"'))
            self.assertIn('3 次巡查 · 2 个日期', index)

    def test_empty_patrol_keeps_past_records_and_date_archive(self):
        self.next['records'] = []
        page = patrol.render(self.next, [self.next, self.first])
        self.assertIn('2 次巡查 · 2 个日期', page)
        self.assertIn('days/2026-11-11.html', page)
        self.assertEqual(len(patrol.aggregate([self.next, self.first])), 6)
        daily_page = patrol.render(self.next, [self.next], mode='day')
        self.assertNotIn('<article class="record"', daily_page)

    def test_scheduled_mode_does_not_relabel_old_manual_snapshot(self):
        self.next['mode'] = '定时巡查'
        page = patrol.render(self.next, [self.next, self.first])
        self.assertIn('最近一轮为定时巡查', page)
        self.assertIn('每天巡查一次，非实时监控', page)
        historical = patrol.render(self.first, [self.first], mode='run')
        self.assertNotIn('定时巡查', historical)
        self.assertIn('当前为手动更新', historical)

    def test_partial_patrol_keeps_other_sources_with_actual_check_dates(self):
        initial = json.loads((patrol.ROOT / 'vivaia-patrol/data/2026-11-10-001.json').read_text())
        retry = json.loads((patrol.ROOT / 'vivaia-patrol/data/2026-11-10-002.json').read_text())
        sources = {s['name']: s for s in patrol.aggregate_sources([retry, initial])}
        self.assertEqual(len(sources), 5)
        self.assertEqual(sources['Trustpilot']['_sequence'], '001')
        self.assertEqual(sources['TikTok']['_sequence'], '002')
        self.assertEqual(sources['TikTok']['status'], retry['sources'][0]['status'])
        self.assertEqual(sources['Google']['_sequence'], '002')
        main = patrol.render(retry, [retry, initial], brand='VIVAIA')
        self.assertIn('最近检查：', main)
        self.assertEqual(len(patrol.aggregate([retry, initial])), 11)
        snapshot = patrol.render(retry, [retry, initial], mode='run', brand='VIVAIA')
        self.assertNotIn('>Trustpilot ↗', snapshot)
        self.assertNotIn('最近检查：', snapshot)
        self.assertEqual(patrol.render(initial, [initial], mode='run', brand='VIVAIA'),
                         patrol.render(initial, [retry, initial], mode='run', brand='VIVAIA'))
        next_day = copy.deepcopy(retry)
        next_day.update(id='2026-11-11-001', date='2026-11-11', sequence='001')
        daily = patrol.render(next_day, [next_day], mode='day', brand='VIVAIA')
        self.assertNotIn('>Trustpilot ↗', daily)
        self.assertIn('2026-11-11 / 001', daily)

    def test_sentiment_update_preserves_historical_classification(self):
        self.next['records'][0]['sentiment_category'] = 'mixed'
        records = patrol.aggregate([self.next, self.first])
        self.assertEqual(records[0]['sentiment_category'], 'mixed')
        self.assertEqual(patrol.aggregate([self.first])[0]['sentiment_category'], 'negative')

    def test_missing_classification_does_not_infer_from_rating(self):
        record = self.first['records'][2]
        self.assertEqual(record['rating'], 5)
        del record['sentiment_category']
        rendered = patrol.render_record(patrol.aggregate([self.first])[2], '')
        self.assertIn('data-sentiment="unknown"', rendered)
        self.assertIn('>未判定</span>', rendered)

    def test_brand_channels_build_independently(self):
        vivaia = json.loads((patrol.ROOT / 'vivaia-patrol/data/2026-11-10-001.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            fanka_dir, vivaia_dir = (Path(directory) / name for name in ('fanka', 'vivaia'))
            for channel, data in [(fanka_dir, self.first), (vivaia_dir, vivaia)]:
                (channel / 'data').mkdir(parents=True)
                (channel / 'data/2026-11-10-001.json').write_text(json.dumps(data))
            patrol.main(channel=fanka_dir)
            before = {p.relative_to(fanka_dir): p.read_bytes() for p in fanka_dir.rglob('*') if p.is_file()}
            patrol.main(channel=vivaia_dir, brand='VIVAIA')
            self.assertEqual(before, {p.relative_to(fanka_dir): p.read_bytes() for p in fanka_dir.rglob('*') if p.is_file()})
            for path in vivaia_dir.rglob('*.html'):
                page = path.read_text()
                self.assertIn('VIVAIA 舆情巡查', page)
                self.assertNotIn('Fanka', page)
                self.assertIn('id="sentiment"', page)
            exported = json.loads((vivaia_dir / 'exports/all.json').read_text())
            self.assertEqual(exported['brand'], 'VIVAIA')
            self.assertEqual(len(exported['records']), len(vivaia['records']))
            self.assertNotIn('tp-delivery', {r['id'] for r in exported['records']})
            with self.assertRaisesRegex(AssertionError, 'different brand'):
                patrol.main(channel=vivaia_dir, brand='Fanka')

    def test_official_posts_without_feedback_leave_current_views_only(self):
        for name, brand, excluded_id, retained_id, expected, sequences in [
            ('fanka-patrol', 'Fanka', 'facebook-tan-powerband', 'instagram-burgundy-comment', 8, ('001', '002')),
            ('vivaia-patrol', 'VIVAIA', 'instagram-cream-sneakers', 'tiktok-shelby-filipa', 12, ('001', '002', '003')),
        ]:
            with self.subTest(brand=brand), tempfile.TemporaryDirectory() as directory:
                channel = Path(directory)
                (channel / 'data').mkdir()
                runs = []
                for sequence in sequences:
                    path = patrol.ROOT / name / 'data' / f'2026-11-10-{sequence}.json'
                    (channel / 'data' / path.name).write_bytes(path.read_bytes())
                    runs.append(json.loads(path.read_text()))
                original = copy.deepcopy(runs)
                patrol.main(channel=channel, brand=brand)
                for filename in ['index.html', 'days/2026-11-10.html']:
                    page = (channel / filename).read_text()
                    self.assertNotIn(f'id="{excluded_id}"', page)
                    self.assertIn(f'id="{retained_id}"', page)
                    self.assertIn('Instagram ↗', page)
                    self.assertIn('Facebook ↗', page)
                for filename in ['exports/all.json', 'exports/daily/2026-11-10.json']:
                    records = json.loads((channel / filename).read_text())['records']
                    self.assertEqual(len(records), expected)
                    self.assertNotIn(excluded_id, {r['id'] for r in records})
                for run in runs:
                    if any(r['id'] == excluded_id for r in run['records']):
                        self.assertIn(f'id="{excluded_id}"',
                                      (channel / 'runs' / f'{run["id"]}.html').read_text())
                self.assertEqual(runs, original)

    def test_official_post_with_new_consumer_feedback_can_enter_records(self):
        run = copy.deepcopy(self.first)
        run['records'] = run['records'][:1]
        run['records'][0].update(publisher_type='brand', consumer_feedback_read=False)
        self.assertEqual(patrol.aggregate([run]), [])
        self.assertEqual(len(patrol.aggregate([run], include_official_only=True)), 1)
        later = copy.deepcopy(run)
        later.update(id='2026-11-11-001', date='2026-11-11')
        later['records'][0]['consumer_feedback_read'] = True
        self.assertEqual(len(patrol.aggregate([run, later])), 1)
        self.assertEqual(len(patrol.aggregate([run, later])[0]['_observations']), 2)
        # A newer observation without feedback must not reveal an older record.
        later['records'][0]['consumer_feedback_read'] = False
        run['records'][0]['consumer_feedback_read'] = True
        self.assertEqual(patrol.aggregate([run, later]), [])


if __name__ == '__main__':
    unittest.main()
