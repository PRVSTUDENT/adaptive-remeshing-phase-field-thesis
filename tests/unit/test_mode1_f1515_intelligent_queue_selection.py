"""Unit tests for Task F1515: Intelligent PBS Queue Selection & Scheduling Architecture.

Validates:
1. Native PBS queue definitions, route mappings, and walltime boundaries.
2. Congestion scoring and walltime admissibility filters.
3. Queue selection ranking on empirical cluster snapshots (favoring dedicated IMFD hardware).
4. PBS scheduler decision hierarchy and non-migration invariants.
5. CLI JSON interface for PowerShell integration.
"""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/hpc'))

import mode1_queue_selector as mqs


class TestMode1F1515IntelligentQueueSelection(unittest.TestCase):
    """Test suite for intelligent PBS queue selection and scheduling invariants."""

    def test_native_pbs_queue_definitions_and_routing_limits(self):
        """Verify known queue parameters, routes, and walltimes match cluster architecture."""
        queues = mqs.KNOWN_QUEUES
        self.assertIn('normal_imfdfkmq', queues)
        self.assertIn('short_imfdfkmq', queues)
        self.assertIn('shortq', queues)
        self.assertIn('mediumq', queues)
        self.assertIn('longq', queues)
        self.assertIn('testq', queues)

        # Route associations
        self.assertEqual(queues['normal_imfdfkmq']['route_via'], 'entry_imfdfkmq')
        self.assertEqual(queues['short_imfdfkmq']['route_via'], 'entry_imfdfkmq')
        self.assertEqual(queues['shortq']['route_via'], 'entryq')
        self.assertEqual(queues['mediumq']['route_via'], 'entryq')
        self.assertEqual(queues['longq']['route_via'], 'entryq')
        self.assertEqual(queues['testq']['route_via'], 'testq')

        # Priorities
        self.assertEqual(queues['normal_imfdfkmq']['priority'], 1000)
        self.assertEqual(queues['short_imfdfkmq']['priority'], 50)
        self.assertEqual(queues['testq']['priority'], 125)
        self.assertEqual(queues['shortq']['priority'], 75)
        self.assertEqual(queues['mediumq']['priority'], 40)
        self.assertEqual(queues['longq']['priority'], 10)

        # Walltimes
        self.assertEqual(queues['normal_imfdfkmq']['max_walltime_hours'], 336)
        self.assertEqual(queues['short_imfdfkmq']['max_walltime_hours'], 12)
        self.assertEqual(queues['shortq']['max_walltime_hours'], 12)
        self.assertEqual(queues['mediumq']['max_walltime_hours'], 36)
        self.assertEqual(queues['longq']['max_walltime_hours'], 168)
        self.assertEqual(queues['testq']['max_walltime_hours'], 4)

    def test_score_queue_walltime_filtering(self):
        """Verify jobs exceeding queue walltime limits are strictly disqualified."""
        telem = {q: {'running': 0, 'queued': 0} for q in mqs.KNOWN_QUEUES}

        # 1-hour job is feasible in all queues
        for q in mqs.KNOWN_QUEUES:
            score, _, expl = mqs.score_queue(q, requested_walltime_hours=1.0, requested_cpus=1, queue_telemetry=telem)
            self.assertGreater(score, 0, f"Queue {q} should be feasible for 1h job: {expl}")

        # 6-hour job: testq (max 4h) disqualified
        score_test, _, _ = mqs.score_queue('testq', requested_walltime_hours=6.0, requested_cpus=1, queue_telemetry=telem)
        self.assertLess(score_test, -1e8, "testq must be disqualified for 6h job")

        # 24-hour job: shortq, short_imfdfkmq, and testq disqualified
        for q in ('shortq', 'short_imfdfkmq', 'testq'):
            score, _, expl = mqs.score_queue(q, requested_walltime_hours=24.0, requested_cpus=1, queue_telemetry=telem)
            self.assertLess(score, -1e8, f"{q} must be disqualified for 24h job: {expl}")

        # 48-hour job: mediumq also disqualified
        score_med, _, _ = mqs.score_queue('mediumq', requested_walltime_hours=48.0, requested_cpus=1, queue_telemetry=telem)
        self.assertLess(score_med, -1e8, "mediumq must be disqualified for 48h job")

    def test_score_queue_priority_and_congestion_dynamics(self):
        """Verify queue scoring responds properly to queue depth and node availability."""
        # Scenario A: Light IMFD congestion (current live state: 2 queued)
        telem_live = {
            'normal_imfdfkmq': {'running': 10, 'queued': 2},
            'shortq': {'running': 9, 'queued': 83},
        }
        idle_live = {'extension2': 0, 'main': 240}

        score_imfd, _, _ = mqs.score_queue('normal_imfdfkmq', 1.0, 1, telem_live, idle_live)
        score_shortq, _, _ = mqs.score_queue('shortq', 1.0, 1, telem_live, idle_live)

        self.assertEqual(score_imfd, 1000 - 10.0 * 2)  # 980
        self.assertEqual(score_shortq, 75 - 10.0 * 83 + 1.5 * 240)  # 75 - 830 + 360 = -395
        self.assertGreater(score_imfd, score_shortq, "normal_imfdfkmq must overwhelmingly outscore congested shortq")

        # Scenario B: Extreme hypothetical IMFD saturation (150 queued) with completely empty shortq
        telem_sat = {
            'normal_imfdfkmq': {'running': 10, 'queued': 150},
            'shortq': {'running': 0, 'queued': 0},
        }
        idle_sat = {'extension2': 0, 'main': 1000}

        score_imfd_sat, _, _ = mqs.score_queue('normal_imfdfkmq', 1.0, 1, telem_sat, idle_sat)
        score_shortq_empty, _, _ = mqs.score_queue('shortq', 1.0, 1, telem_sat, idle_sat)

        self.assertLess(score_imfd_sat, 0, "Heavily congested IMFD queue score must drop")
        self.assertGreater(score_shortq_empty, score_imfd_sat, "Empty general queue should surpass saturated IMFD queue")

    def test_select_best_queue_live_snapshot_favors_dedicated_hardware(self):
        """Verify that under authentic cluster conditions, entry_imfdfkmq is the winning queue."""
        result = mqs.select_best_queue(requested_walltime_hours=1.0, requested_cpus=1)
        self.assertEqual(result['selected_submission_queue'], 'entry_imfdfkmq')
        self.assertEqual(result['selected_execution_queue'], 'normal_imfdfkmq')
        self.assertGreater(result['effective_score'], 1000.0)

        # Confirm rankings order
        rankings = result['rankings']
        self.assertEqual(rankings[0]['execution_queue'], 'normal_imfdfkmq')
        # Confirm shortq is ranked lower due to 83-job queue backlog
        shortq_rank = next(r for r in rankings if r['execution_queue'] == 'shortq')
        self.assertLess(shortq_rank['effective_score'], 0.0)

    def test_scheduler_decision_hierarchy_and_non_migration_invariants(self):
        """Verify the PBS Pro scheduling invariants: no automatic cross-pool migration."""
        # 1. Routing queue is evaluated at submission time only
        # 2. Execution queues cannot dynamically migrate jobs across hardware pools
        # 3. Existing queued jobs 1414558 and 1414563 must remain in normal_imfdfkmq
        imfd_info = mqs.KNOWN_QUEUES['normal_imfdfkmq']
        self.assertTrue(imfd_info['from_route_only'])
        self.assertEqual(imfd_info['node_pool'], 'extension2')
        self.assertEqual(len(imfd_info['nodes']), 10)

        # Confirm that general pool nodes (mnode001..096) do not overlap with extension2 (mnode097..106)
        main_nodes = set(mqs.KNOWN_QUEUES['shortq']['nodes'])
        ext2_nodes = set(imfd_info['nodes'])
        self.assertEqual(len(main_nodes.intersection(ext2_nodes)), 0, "Node pools must be strictly disjoint")

    def test_autoqueue_cli_json_interface(self):
        """Verify the CLI interface produces valid JSON for PowerShell integration."""
        script_path = ROOT / 'scripts/hpc/mode1_queue_selector.py'
        cmd = [sys.executable, str(script_path), '--walltime', '1.0', '--cpus', '1', '--json']
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=10,
        )
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertEqual(data['selected_submission_queue'], 'entry_imfdfkmq')
        self.assertEqual(data['selected_execution_queue'], 'normal_imfdfkmq')
        self.assertIn('rankings', data)
        self.assertEqual(len(data['rankings']), len(mqs.KNOWN_QUEUES))


if __name__ == '__main__':
    unittest.main()
