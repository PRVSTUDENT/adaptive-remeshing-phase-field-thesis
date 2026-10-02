#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic Unit Test for HPC Concurrency Guard
Tests 0, 1, 2, and 3 existing running jobs against a 3-job approved batch.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hpc")))
from guard_batch_submission import get_hpc_job_states, calculate_submission_plan

class TestConcurrencyGuard(unittest.TestCase):
    
    def test_qstat_parsing(self):
        mock_qstat = """
Job id            Name             User              Time Use S Queue
----------------  ---------------- ----------------  -------- - -----
1390533.mmaster02 M2CORR_STAGE_E_  pr21vyci          00:05:14 F normal_imfdfkmq 
1390534.mmaster02 M2CORR_STAGE_E_  pr21vyci          00:05:27 R normal_imfdfkmq 
1390535.mmaster02 M2CORR_STAGE_E_  pr21vyci          00:00:00 Q normal_imfdfkmq 
"""
        res = get_hpc_job_states(mock_qstat)
        self.assertEqual(res["running_count"], 1)
        self.assertEqual(res["queued_count"], 1)
        self.assertIn("1390534.mmaster02", res["running"])
        self.assertIn("1390535.mmaster02", res["queued"])

    def test_zero_running_jobs(self):
        approved = ["Job_1", "Job_2", "Job_3"]
        plan = calculate_submission_plan(0, approved, max_running=2)
        self.assertEqual(plan["available_slots"], 2)
        self.assertEqual(len(plan["immediate_submit_jobs"]), 2)
        self.assertEqual(len(plan["held_or_staged_jobs"]), 1)
        self.assertFalse(plan["submission_plan_causes_breach"])
        self.assertEqual(plan["immediate_submit_jobs"], ["Job_1", "Job_2"])
        self.assertEqual(plan["held_or_staged_jobs"], ["Job_3"])

    def test_one_running_job(self):
        approved = ["Job_1", "Job_2", "Job_3"]
        plan = calculate_submission_plan(1, approved, max_running=2)
        self.assertEqual(plan["available_slots"], 1)
        self.assertEqual(len(plan["immediate_submit_jobs"]), 1)
        self.assertEqual(len(plan["held_or_staged_jobs"]), 2)
        self.assertFalse(plan["submission_plan_causes_breach"])
        self.assertEqual(plan["immediate_submit_jobs"], ["Job_1"])
        self.assertEqual(plan["held_or_staged_jobs"], ["Job_2", "Job_3"])

    def test_two_running_jobs(self):
        approved = ["Job_1", "Job_2", "Job_3"]
        plan = calculate_submission_plan(2, approved, max_running=2)
        self.assertEqual(plan["available_slots"], 0)
        self.assertEqual(len(plan["immediate_submit_jobs"]), 0)
        self.assertEqual(len(plan["held_or_staged_jobs"]), 3)
        self.assertFalse(plan["submission_plan_causes_breach"])
        self.assertEqual(plan["immediate_submit_jobs"], [])
        self.assertEqual(plan["held_or_staged_jobs"], ["Job_1", "Job_2", "Job_3"])

    def test_three_running_jobs_over_capacity(self):
        approved = ["Job_1", "Job_2", "Job_3"]
        plan = calculate_submission_plan(3, approved, max_running=2)
        self.assertEqual(plan["available_slots"], 0)
        self.assertEqual(len(plan["immediate_submit_jobs"]), 0)
        self.assertEqual(len(plan["held_or_staged_jobs"]), 3)
        self.assertFalse(plan["submission_plan_causes_breach"])

if __name__ == "__main__":
    unittest.main()
