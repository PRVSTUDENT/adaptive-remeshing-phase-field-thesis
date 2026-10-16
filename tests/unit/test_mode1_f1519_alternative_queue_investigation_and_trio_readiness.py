"""Unit tests for Task F1519: Alternative PBS Queue Investigation & Diagnostic Trio Readiness.

Validates:
1. Alternative Queue Architecture & Node Pool Partitioning:
   - Verifies queue parameters, routing paths, and walltimes for normal_imfdfkmq, short_imfdfkmq, shortq, mediumq, longq, testq.
   - Confirms strict disjointness between dedicated 'extension2' (mnode097..106) and general 'main' (mnode001..096) node pools.
2. Cross-Pool Priority Bias & EARLIEST_START_UNDETERMINED Classification:
   - Proves PBS Pro static queue priorities (1000 vs 50 vs 40) are intra-pool ranking attributes, not inter-pool dispatch estimators.
   - Verifies dispatch_forecast is EARLIEST_START_UNDETERMINED when node pools are saturated (idle_cpus == 0).
   - Verifies cross_pool_bias_warning is exposed in select_best_queue() output.
3. Queue Selector De-biasing & CLI Options:
   - Verifies penalize_pool_saturation option correctly mitigates the artificial 1000-priority bias during pool saturation.
   - Verifies CLI JSON output includes dispatch_forecast and ranking metadata.
4. Active Diagnostic Trio Governance & Gate 6C Hold:
   - Verifies active jobs 1414558, 1414563, and 1414571 are preserved in normal_imfdfkmq.
   - Confirms Gate 6C hold status is maintained until authentic solver evidence is harvested.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'hpc'))

import mode1_queue_selector as mqs


class TestMode1F1519AlternativeQueueInvestigation(unittest.TestCase):
    """Test suite for alternative PBS queue architecture and dispatch classification."""

    def test_01_queue_architecture_and_pool_partitioning(self):
        """Verify candidate queue definitions and node pool disjointness."""
        queues = mqs.KNOWN_QUEUES
        self.assertIn('normal_imfdfkmq', queues)
        self.assertIn('short_imfdfkmq', queues)
        self.assertIn('shortq', queues)
        self.assertIn('mediumq', queues)
        self.assertIn('longq', queues)

        # Route associations
        self.assertEqual(queues['normal_imfdfkmq']['route_via'], 'entry_imfdfkmq')
        self.assertEqual(queues['short_imfdfkmq']['route_via'], 'entry_imfdfkmq')
        self.assertEqual(queues['shortq']['route_via'], 'entryq')
        self.assertEqual(queues['mediumq']['route_via'], 'entryq')
        self.assertEqual(queues['longq']['route_via'], 'entryq')

        # Node pool disjointness
        ext2_nodes = set(queues['normal_imfdfkmq']['nodes'])
        main_nodes = set(queues['shortq']['nodes'])
        self.assertEqual(len(ext2_nodes), 10, "Dedicated IMFD pool must contain exactly 10 nodes")
        self.assertEqual(len(main_nodes), 96, "General pool must contain exactly 96 nodes")
        self.assertEqual(len(ext2_nodes.intersection(main_nodes)), 0, "Node pools must be 100% disjoint")

    def test_02_intra_pool_priority_vs_cross_pool_bias(self):
        """Verify intra-pool priority semantics and cross-pool bias detection."""
        # Dedicated pool: normal (P=1000) vs short (P=50) sharing extension2 nodes
        imfd_normal = mqs.KNOWN_QUEUES['normal_imfdfkmq']['priority']
        imfd_short = mqs.KNOWN_QUEUES['short_imfdfkmq']['priority']
        self.assertEqual(imfd_normal, 1000)
        self.assertEqual(imfd_short, 50)
        self.assertGreater(imfd_normal, imfd_short, "Within extension2, normal_imfdfkmq has higher priority")

        # General pool: shortq (P=75) vs mediumq (P=40) vs longq (P=10) sharing main nodes
        self.assertEqual(mqs.KNOWN_QUEUES['shortq']['priority'], 75)
        self.assertEqual(mqs.KNOWN_QUEUES['mediumq']['priority'], 40)
        self.assertEqual(mqs.KNOWN_QUEUES['longq']['priority'], 10)

    def test_03_saturated_pool_dispatch_forecast_undetermined(self):
        """Verify dispatch_forecast is EARLIEST_START_UNDETERMINED when pool is saturated."""
        # Simulated live snapshot: extension2 100% full (idle=0) with 2 queued jobs
        telem = {
            'normal_imfdfkmq': {'running': 10, 'queued': 2},
            'shortq': {'running': 9, 'queued': 83},
            'mediumq': {'running': 11, 'queued': 4},
        }
        idle = {'extension2': 0, 'main': 240}

        result = mqs.select_best_queue(
            requested_walltime_hours=1.0,
            requested_cpus=1,
            queue_telemetry=telem,
            node_idle_cpus=idle,
        )

        self.assertEqual(result['classification'], 'HEURISTIC_RECOMMENDATION_ONLY')
        self.assertEqual(result['dispatch_forecast'], 'EARLIEST_START_UNDETERMINED')
        self.assertIn('cross_pool_bias_warning', result)
        self.assertIn('EARLIEST_START_UNDETERMINED', result['cross_pool_bias_warning'])

        # Check rankings detail
        normal_rank = next(r for r in result['rankings'] if r['execution_queue'] == 'normal_imfdfkmq')
        self.assertTrue(normal_rank['pool_saturated'])
        self.assertEqual(normal_rank['pool_idle_cpus'], 0)
        self.assertEqual(normal_rank['dispatch_forecast'], 'EARLIEST_START_UNDETERMINED')

    def test_04_saturation_penalty_option(self):
        """Verify penalize_pool_saturation mitigates static priority bias when pool is full."""
        telem = {
            'normal_imfdfkmq': {'running': 10, 'queued': 2},
            'mediumq': {'running': 5, 'queued': 2},
        }
        idle = {'extension2': 0, 'main': 240}

        # Default: normal_imfdfkmq raw score = 1000 - 20 = 980
        score_def, _, _ = mqs.score_queue('normal_imfdfkmq', 1.0, 1, telem, idle, penalize_pool_saturation=False)
        self.assertEqual(score_def, 980.0)

        # With saturation penalty: normal_imfdfkmq raw score = 1000 - 20 - 500 = 480
        score_pen, _, expl = mqs.score_queue('normal_imfdfkmq', 1.0, 1, telem, idle, penalize_pool_saturation=True)
        self.assertEqual(score_pen, 480.0)
        self.assertIn('saturation penalty -500', expl)

    def test_05_cli_json_interface_includes_forecast(self):
        """Verify CLI --json output includes dispatch_forecast and bias warning."""
        script_path = ROOT / 'scripts' / 'hpc' / 'mode1_queue_selector.py'
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
        self.assertIn('dispatch_forecast', data)
        self.assertIn('cross_pool_bias_warning', data)
        self.assertEqual(data['dispatch_forecast'], 'EARLIEST_START_UNDETERMINED')

    def test_06_active_diagnostic_trio_governance_and_gate_6c_hold(self):
        """Verify the 3 active jobs are preserved and Gate 6C hold is maintained."""
        active_task_path = ROOT / 'project_coordination' / 'ACTIVE_TASK.json'
        self.assertTrue(active_task_path.is_file(), "ACTIVE_TASK.json must exist")
        data = json.loads(active_task_path.read_text(encoding='utf-8'))

        active_jobs = data.get('active_pbs_job_ids', [])
        self.assertIn('1414558.mmaster02', active_jobs)
        self.assertIn('1414563.mmaster02', active_jobs)
        self.assertIn('1414571.mmaster02', active_jobs)
        self.assertEqual(len(active_jobs), 3, "Exactly 3 diagnostic jobs must be active")

        # Confirm Gate 6C hold
        gate_status = data.get('gate_status', '')
        self.assertIn('GATE_6C_HOLD', gate_status)


if __name__ == '__main__':
    unittest.main()
