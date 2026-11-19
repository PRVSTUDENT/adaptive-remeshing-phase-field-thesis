"""Unit test suite for Method C Phase 1 Kickoff.
Verifies demonstration benchmark geometry, bridge rules and policy consistency,
active task state, and kickoff report integrity.
"""
import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest().upper()

def test_kickoff_report_exists_and_geometry():
    report_path = os.path.join(REPO_ROOT, 'docs', 'validation', 'METHOD_C_PHASE1_KICKOFF_REPORT.md')
    assert os.path.isfile(report_path), f"Report missing: {report_path}"

    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON" in content
    assert "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1" in content
    assert "2 December 2026" in content
    assert "13 December 2026" in content
    assert "13 January 2027" in content

    # Geometry checks
    assert "(0.75, 0.50)" in content
    assert "0.10" in content
    assert "0.15" in content
    assert "210.0" in content
    assert "0.0027" in content
    assert "0.0075" in content

def test_bridge_policy_and_rules_consistency():
    policy_path = os.path.join(REPO_ROOT, '.agents', 'scripts', 'bridge_research_policy.json')
    rules_path = os.path.join(REPO_ROOT, '.agents', 'scripts', 'bridge_rules.txt')

    assert os.path.isfile(policy_path)
    assert os.path.isfile(rules_path)

    with open(policy_path, 'r', encoding='utf-8-sig') as f:
        policy = json.load(f)

    with open(rules_path, 'r', encoding='utf-8-sig') as f:
        rules = f.read()

    assert policy['goal_id'] == 'METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1'
    assert policy['method'] == 'METHOD_C'
    assert policy['goal_id'] in rules
    assert "method_c_phase1_demo_and_skeleton" in policy['allowed_operations']

def test_active_task_governance():
    task_path = os.path.join(REPO_ROOT, 'project_coordination', 'ACTIVE_TASK.json')
    assert os.path.isfile(task_path)

    with open(task_path, 'r', encoding='utf-8-sig') as f:
        task = json.load(f)

    assert task['task_id'] == 'METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON'
    assert task['status'] == 'IN_PROGRESS'
    assert task['master_goal_status'] == 'OPEN'
    assert task['max_new_pbs_submissions'] == 0
    assert task['cumulative_pbs_submissions'] == 57

def test_demo_geometry_calculations():
    plate_width = 1.0
    plate_height = 1.0
    notch_x0 = 0.0
    notch_x1 = 0.5
    notch_y = 0.5
    hole_xc = 0.75
    hole_yc = 0.5
    hole_r = 0.10

    inter_ligament = (hole_xc - hole_r) - notch_x1
    rear_ligament = plate_width - (hole_xc + hole_r)

    assert abs(inter_ligament - 0.15) < 1e-9
    assert abs(rear_ligament - 0.15) < 1e-9
    assert notch_y == hole_yc
