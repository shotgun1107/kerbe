from __future__ import annotations

from dataclasses import replace
import json
import unittest

from codex_usage.domain.lifecycle import calculate_deltas, deduplicate_events, DuplicateCheckpointConflict
from codex_usage.sources.codex_jsonl import parse_rollout
from codex_usage.privacy.encoder import UsageEventEncoder


def records(thread, *, baseline=True, fork=True):
    def row(kind, payload):
        return json.dumps({"type": kind, "timestamp": "2026-09-16T00:00:00Z", "payload": payload})
    def token(total):
        return row("event_msg", {"type": "token_count", "info": {
            "total_token_usage": {"input_tokens": total, "output_tokens": 0, "total_tokens": total},
        }})
    meta = {"id": thread}
    if fork:
        meta["forked_from_id"] = "ancestor"
    result = [row("session_meta", meta)]
    if baseline:
        result += [row("compacted", {}), row("turn_context", {"turn_id": "inherited-turn"}), token(100)]
    result += [row("event_msg", {"type": "task_started", "turn_id": "rollout-2"}), token(120), token(150)]
    return result


class LegacyForkCounterTests(unittest.TestCase):
    def test_compacted_fork_prefix_is_baseline_not_parent_usage(self):
        events = calculate_deltas(parse_rollout(records("child")).checkpoints)
        self.assertIsNone(events[0].checkpoint.turn_id)
        self.assertIsNone(events[0].delta)
        self.assertIn("fork_inherited_baseline", events[0].flags)
        self.assertEqual([e.delta.total_tokens for e in events[1:]], [20, 30])

    def test_local_recovery_ids_are_separate_in_memory_and_ledger(self):
        first = calculate_deltas(parse_rollout(records("first")).checkpoints)
        second = calculate_deltas(parse_rollout(records("second")).checkpoints)
        merged = deduplicate_events(first + second)
        self.assertEqual(sum(e.delta.total_tokens for e in merged if e.delta), 100)
        self.assertNotEqual(first[1].logical_key, second[1].logical_key)
        encoder = UsageEventEncoder(b'x' * 32, '00000000-0000-4000-8000-000000000001', parser_version='test')
        self.assertNotEqual(encoder.source_id(first[1]), encoder.source_id(second[1]))
        again = calculate_deltas(parse_rollout(records("first")).checkpoints)
        self.assertEqual(encoder.source_id(first[1]), encoder.source_id(again[1]))

    def test_missing_fork_prefix_never_counts_inherited_total(self):
        events = calculate_deltas(parse_rollout(records("child", baseline=False)).checkpoints)
        self.assertIsNone(events[0].delta)
        self.assertIn("fork_missing_baseline", events[0].flags)
        self.assertEqual(events[1].delta.total_tokens, 30)
        ordinary = calculate_deltas(parse_rollout(records("ordinary", baseline=False, fork=False)).checkpoints)
        self.assertEqual(ordinary[0].delta.total_tokens, 120)

    def test_identical_checkpoint_can_recover_only_unknown_delta(self):
        events = calculate_deltas(parse_rollout(records("child")).checkpoints)
        known = events[1]
        missing = replace(known, delta=None, flags=("fork_missing_baseline",))
        for pair in ([known, missing], [missing, known]):
            result = deduplicate_events(pair)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].delta.total_tokens, 20)
            self.assertNotIn("fork_missing_baseline", result[0].flags)
        conflicting = replace(known, delta=known.checkpoint.cumulative)
        with self.assertRaises(DuplicateCheckpointConflict):
            deduplicate_events([known, conflicting])
