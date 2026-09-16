from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from codex_usage.cli import main
from codex_usage.reports.quota import render_quota
from codex_usage.sources.quota import QuotaError, find_codex, read_rate_limits


NOW = datetime(2026, 9, 16, 0, 0, tzinfo=timezone.utc)
WINDOW = {"usedPercent": 25, "windowDurationMins": 300, "resetsAt": NOW.timestamp() + 3600}
RESPONSE = {"rateLimitsByLimitId": {
    "codex": {"primary": WINDOW, "secondary": {**WINDOW, "windowDurationMins": 10080}},
    "other": {"limitName": "Separate model", "primary": {**WINDOW, "usedPercent": 90}},
}, "rateLimits": {"primary": {**WINDOW, "usedPercent": 99}}}


class QuotaRenderingTests(unittest.TestCase):
    def test_multiple_buckets_prefer_map_and_render_kst_reset(self):
        result = render_quota(RESPONSE, observed_at=NOW)
        self.assertIn("남음 75%", result)
        self.assertIn("남음 10%", result)
        self.assertNotIn("사용 99%", result)
        self.assertIn("5시간 (primary)", result)
        self.assertIn("7일 (secondary)", result)
        self.assertIn("2026-09-16 10:00:00 KST", result)
        self.assertIn("0일 1시간 0분 후", result)

    def test_legacy_and_missing_fields_do_not_invent_zero(self):
        result = render_quota({"rateLimits": {"primary": {}}}, observed_at=NOW)
        self.assertIn("남음 미제공", result)
        self.assertIn("초기화: 미제공", result)
        self.assertNotIn("0%", result)
        self.assertIn("한도 정보 없음", render_quota({"rateLimits": None}))
        self.assertIn("한도 창 정보 미제공", render_quota({"rateLimits": {}}))

    def test_empty_map_does_not_reuse_legacy_bucket(self):
        result = render_quota({"rateLimitsByLimitId": {}, "rateLimits": {"primary": WINDOW}})
        self.assertIn("한도 정보 없음", result)
        self.assertNotIn("75%", result)

    def test_bad_numbers_expired_reset_and_terminal_controls(self):
        for used in (None, True, "25", float("nan"), float("inf"), -1, 10**1000):
            with self.subTest(used=str(used)[:20]):
                result = render_quota({"rateLimits": {"primary": {**WINDOW, "usedPercent": used}}})
                self.assertIn("남음 미제공", result)
        result = render_quota({"rateLimits": {
            "limitName": "test\x1b\nname", "primary": {**WINDOW, "usedPercent": 110, "resetsAt": 0},
        }}, observed_at=NOW)
        self.assertIn("남음 0%", result)
        self.assertIn("지난 시각", result)
        self.assertNotIn("\x1b", result)
        self.assertIn("testname", result)

    def test_malformed_structure_and_timezone_fail_explicitly(self):
        for response in ({"rateLimitsByLimitId": []}, {"rateLimits": []}, {"rateLimits": {"primary": 4}}):
            with self.subTest(response=response), self.assertRaises(QuotaError):
                render_quota(response)
        with self.assertRaises(QuotaError):
            render_quota(RESPONSE, timezone_name="not/a/timezone")


class QuotaTransportTests(unittest.TestCase):
    def test_explicit_path_and_path_lookup_take_priority(self):
        with patch("codex_usage.sources.quota.shutil.which", return_value="chosen.exe"):
            self.assertEqual(find_codex("codex"), "chosen.exe")
        with patch("codex_usage.sources.quota.shutil.which", return_value=None):
            self.assertIsNone(find_codex("explicit-missing.exe"))

    @unittest.skipUnless(os.name == "nt", "Windows desktop discovery")
    def test_windows_desktop_discovery_without_path_uses_newest_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            older = root / "Programs/Codex/resources/codex.exe"
            newer = root / "Programs/CodexPersonal/1.2/app/resources/codex.exe"
            for stamp, path in enumerate((older, newer), start=1):
                path.parent.mkdir(parents=True)
                path.touch()
                os.utime(path, (stamp, stamp))
            with patch.dict(os.environ, {"LOCALAPPDATA": directory}), patch(
                "codex_usage.sources.quota.shutil.which", return_value=None,
            ):
                self.assertEqual(find_codex("codex"), str(newer))
                self.assertIsNone(find_codex("explicit-missing.exe"))

    def run_server(self, ending: str, timeout: float = 5):
        # Real pipes/process lifecycle, but only a synthetic stdio server, no login/network.
        script = '''
import json, sys, time
def read(): return json.loads(sys.stdin.readline())
def send(value): print(json.dumps(value), flush=True)
first = read()
assert first['method'] == 'initialize'
send({'id': 1, 'result': {}})
assert read()['method'] == 'initialized'
assert read()['method'] == 'account/rateLimits/read'
''' + ending
        spawn = asyncio.create_subprocess_exec
        processes = []

        async def fake_spawn(*args, **kwargs):
            self.assertEqual(args[1:], ("app-server",))
            process = await spawn(sys.executable, "-u", "-c", script, **kwargs)
            processes.append(process)
            return process

        with patch("codex_usage.sources.quota.asyncio.create_subprocess_exec", side_effect=fake_spawn):
            try:
                return read_rate_limits(executable=sys.executable, timeout=timeout)
            finally:
                self.assertTrue(processes)
                self.assertIsNotNone(processes[0].returncode)

    def test_handshake_notifications_server_request_and_cleanup(self):
        result = self.run_server('''
send({'method': 'account/rateLimits/updated', 'params': {}})
send({'id': 88, 'method': 'unexpected/request'})
assert read()['error']['code'] == -32601
send({'id': 99, 'result': {}})
send({'id': 2, 'result': ''' + repr(RESPONSE) + '''})
time.sleep(30)
''')
        self.assertEqual(result, RESPONSE)

    def test_error_does_not_leak_account_or_server_details(self):
        with self.assertRaises(QuotaError) as caught:
            self.run_server("send({'id': 2, 'error': {'message': 'SECRET ACCOUNT TOKEN'}})")
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertIn("로그인", str(caught.exception))

    def test_eof_and_malformed_protocol(self):
        for ending in ("sys.exit(0)", "print('not json', flush=True)", "send({'id': 2, 'result': None})"):
            with self.subTest(ending=ending), self.assertRaises(QuotaError):
                self.run_server(ending)

    def test_timeout_terminates_child(self):
        with self.assertRaisesRegex(QuotaError, "시간이 초과"):
            self.run_server("time.sleep(30)", timeout=0.5)

    def test_missing_executable_and_invalid_timeouts(self):
        with self.assertRaisesRegex(QuotaError, "실행 파일"):
            read_rate_limits(executable="missing-codex-for-test-abcdef")
        for timeout in (0, -1, float("nan"), float("inf"), 121):
            with self.subTest(timeout=timeout), self.assertRaises(QuotaError):
                read_rate_limits(timeout=timeout)


class QuotaCliTests(unittest.TestCase):
    def test_status_without_config_or_secret_store(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "absent.json"
            output = StringIO()
            with patch("codex_usage.cli.main.read_rate_limits", return_value=RESPONSE) as query, patch(
                "codex_usage.cli.main.default_secret_store", side_effect=AssertionError("secret accessed"),
            ):
                code = main(["--config", str(config), "status", "--timeout", "3", "--timezone", "UTC"], stdout=output)
            self.assertEqual(code, 0)
            query.assert_called_once_with(executable="codex", timeout=3)
            self.assertIn("남음 75%", output.getvalue())
            self.assertFalse(config.exists())

    def test_failures_have_nonzero_exit_and_no_false_quota(self):
        output, errors = StringIO(), StringIO()
        with patch("codex_usage.cli.main.read_rate_limits", side_effect=QuotaError("조회 실패")):
            code = main(["status"], stdout=output, stderr=errors)
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("조회 실패", errors.getvalue())

    def test_invalid_timezone_does_not_start_query(self):
        with patch("codex_usage.cli.main.read_rate_limits") as query:
            code = main(["status", "--timezone", "bad/timezone"], stderr=StringIO())
        self.assertEqual(code, 2)
        query.assert_not_called()
