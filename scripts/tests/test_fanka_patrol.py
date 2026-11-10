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


if __name__ == '__main__':
    unittest.main()
