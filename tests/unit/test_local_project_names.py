from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from codex_usage.privacy.identifiers import project_id
from codex_usage.ledger.replay import replay_ledger_events
from codex_usage.storage.sqlite import LocalStateStore
from codex_usage.storage.project_names import remember_project_names, load_local_project_names
from codex_usage.reports.query import ReportQuery, build_usage_report
from tests.ledger_events import usage_event, mapping_event, opaque


class LocalProjectNameTests(unittest.TestCase):
    def test_local_names_survive_rebuild_without_entering_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.sqlite'
            key = b'x' * 32
            pid = project_id(key, 'github.com/owner/repository')
            store = LocalStateStore(path)
            event = usage_event(project_id=pid, total=100)
            replay = replay_ledger_events([event])
            store.rebuild_read_model(replay)
            remember_project_names(path, key, ['github.com/owner/repository'])
            store.rebuild_read_model(replay)
            report = build_usage_report(path, ReportQuery(group_by=('project',)))
            self.assertEqual(report.rows[0].dimensions['project'], 'owner/repository')
            self.assertEqual(report.total.total_tokens.value, 100)
            self.assertEqual(build_usage_report(path, ReportQuery(project='owner/repository')).total.total_tokens.value, 100)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('select count(*) from mapping_events').fetchone()[0], 0)
                self.assertEqual(db.execute('select count(*) from outbox_events').fetchone()[0], 0)

    def test_manual_label_overrides_automatic_name(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.sqlite'
            key = b'x' * 32
            pid = project_id(key, 'github.com/owner/repository')
            store = LocalStateStore(path)
            name = mapping_event(kind='project_name', subject_type='project', subject_id=pid,
                                 target_project_id=None, display_value='My project')
            store.rebuild_read_model(replay_ledger_events([usage_event(project_id=pid), name]))
            remember_project_names(path, key, ['github.com/owner/repository'])
            report = build_usage_report(path, ReportQuery(group_by=('project',)))
            self.assertEqual(report.rows[0].dimensions['project'], 'My project')

    def test_old_database_and_non_github_hosts(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.sqlite'
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(load_local_project_names(db), {})
            remember_project_names(path, b'x' * 32, ['git.example.com/team/repo', 'prj_h1_opaque'])
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(list(load_local_project_names(db).values()), ['git.example.com/team/repo'])
