"""Patrol routing and publish-before-send gate; all network calls are mocked."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import notify_patrol as sender

WEBHOOK = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=fixture-only'


class PatrolNotificationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        original_root = sender.ROOT
        self.enterContext(patch.object(sender, 'ROOT', self.root))
        self.enterContext(patch.dict(os.environ, {
            'GITHUB_REF': 'refs/heads/main', 'PATROL_WEBHOOK': WEBHOOK,
            'GITHUB_RUN_ATTEMPT': '1', 'WECOM_WEBHOOK': 'old-robot-must-not-be-used',
            'WECOM_WEBHOOK_VIVAIA': 'old-vivaia-must-not-be-used',
            'WECOM_WEBHOOK_TEST': 'test-must-not-be-used',
        }, clear=True))
        self.urlopen = self.enterContext(patch.object(sender.urllib.request, 'urlopen'))
        self.opener = self.enterContext(patch.object(sender.urllib.request, 'build_opener'))
        response = self.opener.return_value.open.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = b'{"errcode":0}'
        self.data = json.loads((original_root / 'fanka-patrol/data/2026-11-10-001.json').read_text())
        self.write(self.data)

    def write(self, run, channel='fanka'):
        for folder, suffix, content in [('data', 'json', json.dumps(run)), ('runs', 'html', '<html>fixture</html>')]:
            path = self.root / f'{channel}-patrol' / folder / f'{run["id"]}.{suffix}'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def preview(self, run_id='2026-11-10-001', channel='fanka'):
        payload, pages = sender.prepare(channel, run_id)
        return json.loads(payload)['markdown']['content'], pages

    def test_history_counts_official_exclusion_and_no_future_leak(self):
        run = copy.deepcopy(self.data)
        run.update(id='2026-11-11-001', date='2026-11-11', sequence='001', coverage_status='partial')
        run['records'] = run['records'][:2]
        run['records'][1].update(url='https://example.org/new', publisher_type='brand', consumer_feedback_read=False)
        self.write(run)
        content, _ = self.preview(run['id'])
        self.assertIn('首次收录 0 条 · 复查 1 条', content)
        first, _ = self.preview()
        self.assertIn('首次收录 6 条 · 复查 0 条', first)
        self.assertIn('部分渠道或评论访问受限', content)

    def test_brand_mismatch_and_path_traversal_refused(self):
        for run_id in ['../2026-11-10-001', '2026-13-40-001', '2026-11-10-000']:
            with self.assertRaises(ValueError):
                sender.prepare('fanka', run_id)
        self.write(self.data, channel='vivaia')
        with self.assertRaises(sender.ConfigurationError):
            sender.prepare('vivaia', self.data['id'])

    def test_vivaia_links_and_routing(self):
        run = copy.deepcopy(self.data)
        run['brand'] = 'VIVAIA'
        self.write(run, 'vivaia')
        content, pages = self.preview(channel='vivaia')
        self.assertIn('VIVAIA 舆情巡查', content)
        self.assertNotIn('/fanka-patrol/', content)
        self.assertTrue(all('/vivaia-patrol/' in url for url, _ in pages))
        self.assertEqual(sender.CHANNELS['vivaia'][1], 'WECOM_WEBHOOK_VIVAIA_PATROL')

    def test_dry_run_requires_no_secret_and_performs_no_network(self):
        os.environ.pop('PATROL_WEBHOOK')
        with contextlib.redirect_stdout(io.StringIO()) as out:
            sender.main(['--channel', 'fanka', '--run-id', self.data['id'], '--dry-run'])
        self.assertIn('DRY RUN', out.getvalue())
        self.urlopen.assert_not_called()
        self.opener.assert_not_called()

    def test_missing_secret_never_uses_old_robots(self):
        os.environ.pop('PATROL_WEBHOOK')
        with self.assertRaisesRegex(SystemExit, 'WECOM_WEBHOOK_FANKA_PATROL missing'):
            sender.main(['--channel', 'fanka', '--run-id', self.data['id']])
        self.urlopen.assert_not_called()
        self.opener.assert_not_called()

    def test_webhook_validation(self):
        for value in ['https://example.org/?key=x', WEBHOOK + '&key=extra', WEBHOOK + '#fragment', WEBHOOK + '\nextra']:
            os.environ['PATROL_WEBHOOK'] = value
            with self.assertRaises(sender.ConfigurationError):
                sender.webhook_for('fanka')

    def test_non_main_and_workflow_rerun_refused(self):
        for key, value in [('GITHUB_REF', 'refs/heads/feature'), ('GITHUB_RUN_ATTEMPT', '2')]:
            with patch.dict(os.environ, {key: value}), self.assertRaises(SystemExit):
                sender.main(['--channel', 'fanka', '--run-id', self.data['id']])
        self.opener.assert_not_called()

    def test_added_runs_uses_exact_diff_no_all_files_fallback(self):
        with patch.object(sender.subprocess, 'check_output', return_value='fanka-patrol/data/2026-11-11-001.json\n') as git:
            self.assertEqual(sender.added_runs('fanka', 'a' * 40, 'b' * 40), ['2026-11-11-001'])
            self.assertIn('--diff-filter=A', git.call_args.args[0])
            self.assertIn('--no-renames', git.call_args.args[0])
        with self.assertRaises(sender.ConfigurationError):
            sender.added_runs('fanka', '0' * 40, 'b' * 40)

    def test_stale_http_200_blocks_send(self):
        response = self.urlopen.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = b'old content'
        _, pages = self.preview()
        with self.assertRaises(TimeoutError):
            sender.wait_for_pages(pages, timeout=0)
        self.opener.assert_not_called()

    def test_matching_snapshot_and_json_then_send(self):
        _, pages = self.preview()
        bodies = {url: path.read_bytes() for url, path in pages}
        def page_response(request, **kwargs):
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = 200
            response.read.return_value = bodies[request.full_url.split('?')[0]]
            return response
        self.urlopen.side_effect = page_response
        with contextlib.redirect_stdout(io.StringIO()) as out:
            sender.main(['--channel', 'fanka', '--run-id', self.data['id']])
        self.assertEqual(self.urlopen.call_count, 2)
        self.opener.return_value.open.assert_called_once()
        self.assertIn('target=WECOM_WEBHOOK_FANKA_PATROL; errcode=0', out.getvalue())
        request = self.opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, WEBHOOK)

    def test_page_failure_prevents_post(self):
        with patch.object(sender, 'wait_for_pages', side_effect=TimeoutError), self.assertRaises(SystemExit):
            sender.main(['--channel', 'fanka', '--run-id', self.data['id']])
        self.opener.assert_not_called()

    def test_api_and_network_errors_do_not_leak_secret_or_retry(self):
        response = self.opener.return_value.open.return_value.__enter__.return_value
        response.read.return_value = b'{"errcode":93000}'
        with self.assertRaises(sender.ConfigurationError) as failure:
            sender.send('fanka', self.data['id'], WEBHOOK, b'{}')
        self.assertNotIn('fixture-only', str(failure.exception))
        self.opener.reset_mock()
        self.opener.return_value.open.side_effect = OSError(WEBHOOK)
        with self.assertRaises(sender.ConfigurationError) as failure:
            sender.send('fanka', self.data['id'], WEBHOOK, b'{}')
        self.assertNotIn('fixture-only', str(failure.exception))
        self.opener.return_value.open.assert_called_once()

    def test_redirect_refused(self):
        request = sender.urllib.request.Request(WEBHOOK)
        with self.assertRaises(urllib.error.HTTPError) as failure:
            sender.NoRedirect().redirect_request(request, None, 302, '', {}, 'https://example.org/')
        failure.exception.close()

    def test_blocked_patrol_with_records_refused(self):
        self.data['coverage_status'] = 'blocked'
        self.write(self.data)
        with self.assertRaisesRegex(sender.ConfigurationError, 'Blocked patrol'):
            self.preview()

    def test_long_external_titles_cannot_add_mentions_and_fit_message(self):
        for record in self.data['records']:
            record.update(title='<@all> [injected](https://example.org) ' + '中' * 4000, priority=True)
        self.write(self.data)
        content, _ = self.preview()
        self.assertNotIn('<@all>', content)
        self.assertNotIn('[injected]', content)
        self.assertLess(len(content.encode()), 4000)

    def test_empty_partial_patrol_not_reported_as_no_sentiment(self):
        self.data.update(records=[], coverage_status='blocked')
        self.write(self.data)
        content, _ = self.preview()
        self.assertIn('本轮未取得可核实正文', content)
        self.assertIn('不代表全网没有新评价', content)
        self.assertLess(len(content.encode()), 4000)


if __name__ == '__main__':
    unittest.main()
