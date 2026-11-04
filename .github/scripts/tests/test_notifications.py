import contextlib
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
import notify
import notify_test as sender

TEST_WEBHOOK = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-only-placeholder'


class NotificationIsolationTests(unittest.TestCase):
    def setUp(self):
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(contextlib.chdir(temporary))
        env = {'GITHUB_REF': 'refs/heads/main', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
               'TEST_CHANNEL': 'vivaia', 'WECOM_WEBHOOK_TEST': TEST_WEBHOOK}
        for channel in ('TECH', 'BUSINESS', 'FITNESS', 'FANKA_SOCIAL', 'VIVAIA'):
            env[f'WECOM_WEBHOOK_{channel}'] = f'https://example.com/production-{channel}'
            env[f'WECOM_MENTION_{channel}'] = '@all'
            env[f'WECOM_MENTION_MSG_{channel}'] = 'production mention'
        self.enterContext(patch.dict(os.environ, env, clear=True))
        self.data = self.create_report('vivaia')
        # Mock all network entry points. No real robot or page requests can escape.
        self.urlopen = self.enterContext(patch('urllib.request.urlopen', side_effect=self.page_response))
        self.opener_factory = self.enterContext(patch('urllib.request.build_opener'))
        self.open = self.opener_factory.return_value.open
        response = self.open.return_value.__enter__.return_value
        response.status = 200
        response.read.return_value = b'{"errcode": 0}'

    def create_report(self, channel):
        directory = Path('test', channel)
        directory.mkdir(parents=True, exist_ok=True)
        directory.joinpath('index.html').write_text(f'<html><body>【测试】{channel}</body></html>')
        data = {'environment': 'test', 'channel': channel, 'edition': '0001',
                'date': '2026年11月4日 09:00', 'intro': '测试导语',
                'tags': ['一', '二', '三', '四', '五'], 'page': 'index.html',
                'top3': [{'title': f'趋势{i}', 'comment': '点评', 'url': f'https://example.com/{i}'} for i in range(3)],
                'blog_url': 'https://example.com/production-blog'}
        self.write_data(data, channel)
        return data

    def write_data(self, data=None, channel='vivaia'):
        Path('test', channel, 'latest.json').write_text(json.dumps(data or self.data))

    def page_response(self, request, **_):
        self.assertTrue(request.full_url.startswith(sender.TEST_BASE_URL))
        relative = request.full_url[len(sender.TEST_BASE_URL):].split('?')[0]
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = Path('test', relative).read_bytes()
        return response

    def run_sender(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            sender.main()
        return output.getvalue()

    def assert_preflight_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_sender()
        self.open.assert_not_called()
        self.urlopen.assert_not_called()

    def test_all_five_channels_use_only_the_shared_test_robot(self):
        for channel in sender.CHANNELS:
            self.create_report(channel)
        os.environ['TEST_CHANNEL'] = 'all'
        output = self.run_sender()
        self.assertEqual(self.open.call_count, 5)
        for call in self.open.call_args_list:
            req = call.args[0]
            self.assertEqual(req.full_url, TEST_WEBHOOK)
            content = json.loads(req.data)['markdown']['content']
            self.assertIn('【测试】', content)
            self.assertIn('/ai-news-daily/test/', content)
            self.assertNotIn('<@', content)
            self.assertNotIn('production mention', content)
            self.assertNotIn('production-blog', content)
        self.assertEqual(output.count('target=WECOM_WEBHOOK_TEST; errcode=0'), 5)
        self.assertNotIn('test-only-placeholder', output)

    def test_push_selects_only_changed_test_channel(self):
        self.create_report('fitness')
        Path('changed.txt').write_text('test/vivaia/index.html\nfitness/index.html\nlatest-fitness.json\n')
        os.environ.update(GITHUB_EVENT_NAME='push', CHANGED_FILES_PATH='changed.txt')
        self.run_sender()
        self.open.assert_called_once()
        self.assertIn('VIVAIA', json.loads(self.open.call_args.args[0].data)['markdown']['content'])

    def test_production_only_changes_never_send_to_test_robot(self):
        Path('changed.txt').write_text('vivaia/index.html\nlatest-vivaia.json\n')
        os.environ.update(GITHUB_EVENT_NAME='push', CHANGED_FILES_PATH='changed.txt')
        self.assertIn('No test reports', self.run_sender())
        self.open.assert_not_called()
        self.urlopen.assert_not_called()

    def test_preview_without_json_deploys_without_sending(self):
        Path('test/vivaia/latest.json').unlink()
        Path('changed.txt').write_text('test/vivaia/index.html\n')
        os.environ.update(GITHUB_EVENT_NAME='push', CHANGED_FILES_PATH='changed.txt')
        self.assertIn('preview-only', self.run_sender())
        self.open.assert_not_called()
        self.urlopen.assert_not_called()

    def test_missing_test_secret_never_falls_back(self):
        for secret in ('', '   '):
            with self.subTest(secret=secret), patch.dict(os.environ, {'WECOM_WEBHOOK_TEST': secret}):
                self.assert_preflight_rejected()

    def test_test_branch_and_missing_ref_are_rejected(self):
        for ref in ('refs/heads/vivaia-test', 'refs/tags/main', ''):
            with self.subTest(ref=ref), patch.dict(os.environ, {'GITHUB_REF': ref}):
                self.assert_preflight_rejected()

    def test_multiple_or_invalid_webhooks_are_rejected(self):
        for value in (TEST_WEBHOOK + ',' + TEST_WEBHOOK, 'https://example.com/hook',
                      TEST_WEBHOOK.replace('https:', 'http:'), TEST_WEBHOOK + '&key=second'):
            with self.subTest(value=value), patch.dict(os.environ, {'WECOM_WEBHOOK_TEST': value}):
                self.assert_preflight_rejected()

    def test_wrong_environment_or_channel_is_rejected(self):
        for key, value in (('environment', None), ('environment', 'production'), ('channel', 'fitness')):
            with self.subTest(key=key, value=value):
                self.write_data(dict(self.data, **{key: value}))
                self.assert_preflight_rejected()

    def test_missing_or_invalid_json_is_rejected(self):
        Path('test/vivaia/latest.json').unlink()
        self.assert_preflight_rejected()
        Path('test/vivaia/latest.json').write_text('{bad')
        self.assert_preflight_rejected()
        self.write_data(dict(self.data, top3=[]))
        self.assert_preflight_rejected()

    def test_formal_urls_and_paths_cannot_be_used(self):
        invalid = [('url', 'https://baldmuzi.github.io/ai-news-daily/vivaia/edition-0114.html'),
                   ('page', '../../vivaia/edition-0114.html'), ('page', '/vivaia/index.html'),
                   ('page', 'https://example.com/page'), ('page', 'missing.html')]
        for key, value in invalid:
            with self.subTest(key=key, value=value):
                self.write_data(dict(self.data, **{key: value}))
                self.assert_preflight_rejected()

    def test_fanka_blog_links_stay_in_test_channel(self):
        data = self.create_report('fitness')
        Path('test/fitness/blog.html').write_text('<html>Test blog</html>')
        self.write_data(dict(data, blog_page='blog.html', blog_title='测试博客'), 'fitness')
        _, payload, pages = sender.prepare_notification('fitness')
        content = json.loads(payload)['markdown']['content']
        self.assertIn('/test/fitness/blog.html', content)
        self.assertEqual(len(pages), 3)
        self.assertNotIn('production-blog', content)

    def test_200_with_stale_content_is_not_ready(self):
        response = self.page_response(MagicMock(full_url=sender.TEST_BASE_URL + 'vivaia/index.html'))
        response.read.return_value = b'old version'
        self.urlopen.side_effect = None
        self.urlopen.return_value = response
        with self.assertRaises(TimeoutError):
            sender.wait_for_test_pages([(sender.TEST_BASE_URL + 'vivaia/index.html', Path('test/vivaia/index.html'))], timeout=0)
        self.open.assert_not_called()

    def test_page_timeout_prevents_every_notification(self):
        with patch.object(sender, 'wait_for_test_pages', side_effect=TimeoutError('not deployed')):
            with self.assertRaises(SystemExit):
                self.run_sender()
        self.open.assert_not_called()

    def test_all_data_is_validated_before_first_send(self):
        self.create_report('fitness')
        self.write_data(dict(self.data, environment='production'))
        os.environ['TEST_CHANNEL'] = 'all'
        self.assert_preflight_rejected()

    def test_api_rejection_never_claims_success(self):
        self.open.return_value.__enter__.return_value.read.return_value = b'{"errcode": 93000}'
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            sender.main()
        self.open.assert_called_once()
        self.assertNotIn('notification sent', output.getvalue())

    def test_network_error_does_not_leak_secret_or_retry(self):
        self.open.side_effect = urllib.error.URLError(TEST_WEBHOOK)
        with self.assertRaises(SystemExit) as error:
            self.run_sender()
        self.assertNotIn('test-only-placeholder', str(error.exception))
        self.open.assert_called_once()

    def test_redirect_and_http_error_are_not_followed_or_retried(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            sender.NoRedirect().redirect_request(MagicMock(full_url=TEST_WEBHOOK), None, 302, '', {}, 'https://example.com')
        error.exception.close()
        self.open.side_effect = urllib.error.HTTPError(TEST_WEBHOOK, 302, TEST_WEBHOOK, {}, None)
        with self.assertRaises(SystemExit) as error:
            self.run_sender()
        self.assertNotIn('test-only-placeholder', str(error.exception))
        self.open.assert_called_once()

    def test_test_directory_does_not_select_any_production_robot(self):
        with patch.object(notify, 'load_changed_files', return_value={'test/vivaia/latest.json', 'test/fitness/index.html'}), \
             patch.object(notify, 'post_wecom') as post, patch.dict(os.environ, {'GITHUB_EVENT_NAME': 'push'}), \
             contextlib.redirect_stdout(io.StringIO()):
            notify.main()
        post.assert_not_called()

    def test_production_route_still_uses_existing_vivaia_webhook(self):
        with patch.object(notify, 'load_changed_files', return_value={'latest-vivaia.json'}), \
             patch.object(notify, 'post_wecom') as post, patch.dict(os.environ, {'GITHUB_EVENT_NAME': 'push'}), \
             contextlib.redirect_stdout(io.StringIO()):
            notify.main()
        post.assert_called_once_with('https://example.com/production-VIVAIA', 'latest-vivaia.json',
                                    'VIVAIA 品牌趋势', 'WECOM_MENTION_VIVAIA')

    def test_production_sender_rejects_test_marked_data(self):
        with self.assertRaises(SystemExit):
            notify.post_wecom('https://example.com/production', 'test/vivaia/latest.json', 'VIVAIA', 'WECOM_MENTION_VIVAIA')
        self.urlopen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
