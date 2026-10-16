"""Intelligent PBS Queue Selection & Congestion Scoring for Mode-I HPC Experiments.

Classification: HEURISTIC_RECOMMENDATION_ONLY
Status: HEURISTIC_RECOMMENDATION_ONLY until production execution is verified.

Evaluates dedicated IMFD hardware queues vs general cluster queues using
empirical queue priority, queue depth, node pool availability, and requested
resources (walltime, CPUs, memory).

Note on Scheduler Privacy Boundary:
PBS Pro on mmaster02 enforces 'query_other_jobs = False', which prevents
standard users from inspecting start times or remaining walltimes of other users'
jobs. Therefore, earliest-start forecasting without dummy probe submissions is
bounded to heuristic scoring:
    Score = Priority - (10.0 * queued_jobs) + (1.5 * idle_cpus) + Bonus(dedicated)
This score provides a comparative ranking metric and is formally classified as
HEURISTIC_RECOMMENDATION_ONLY.

Note on Intra-Pool vs Inter-Pool Queue Priority Bias:
In PBS Pro, queue priority (e.g. 1000 for normal_imfdfkmq vs 50 for short_imfdfkmq
vs 40 for mediumq vs 75 for shortq) is an INTRA-POOL ranking attribute used by the
scheduler to resolve contention among jobs competing for the SAME node pool.
The scheduler never compares normal_imfdfkmq against mediumq because their node sets
(extension2 vs main) are 100% disjoint (disjoint Qlists).
When a node pool is 100% saturated (e.g. extension2 with 0 idle CPUs), comparing raw
static priorities across disjoint pools creates an artificial mathematical bias
favoring normal_imfdfkmq despite dispatch delays.
Because PBS Pro enforces 'query_other_jobs = False', remaining walltimes of active jobs
are unobservable. Thus, any cross-pool dispatch forecast during pool saturation is
formally:
    EARLIEST_START_UNDETERMINED

Supports offline simulation for testing as well as live cluster evaluation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

CLASSIFICATION = "HEURISTIC_RECOMMENDATION_ONLY"
DISPATCH_FORECAST_UNDETERMINED = "EARLIEST_START_UNDETERMINED"
DISPATCH_FORECAST_IMMEDIATE = "IMMEDIATE_DISPATCH_CAPACITY_AVAILABLE"
DISPATCH_FORECAST_QUEUED = "QUEUED_PENDING_DISPATCH"

# Static configuration of known queues on TU Freiberg HPC (mmaster02)
KNOWN_QUEUES = {
    'normal_imfdfkmq': {
        'type': 'Execution',
        'route_via': 'entry_imfdfkmq',
        'priority': 1000,
        'max_walltime_hours': 336,
        'node_pool': 'extension2',
        'dedicated_to': 'IMFD-FKM',
        'nodes': ['mnode097', 'mnode098', 'mnode099', 'mnode100', 'mnode101',
                  'mnode102', 'mnode103', 'mnode104', 'mnode105', 'mnode106'],
        'from_route_only': True,
    },
    'short_imfdfkmq': {
        'type': 'Execution',
        'route_via': 'entry_imfdfkmq',
        'priority': 50,
        'max_walltime_hours': 12,
        'node_pool': 'extension2',
        'dedicated_to': 'IMFD-FKM',
        'nodes': ['mnode097', 'mnode098', 'mnode099', 'mnode100', 'mnode101',
                  'mnode102', 'mnode103', 'mnode104', 'mnode105', 'mnode106'],
        'from_route_only': True,
    },
    'shortq': {
        'type': 'Execution',
        'route_via': 'entryq',
        'priority': 75,
        'max_walltime_hours': 12,
        'node_pool': 'main',
        'dedicated_to': 'general',
        'nodes': [f'mnode{i:03d}' for i in range(1, 97)],
        'from_route_only': True,
    },
    'mediumq': {
        'type': 'Execution',
        'route_via': 'entryq',
        'priority': 40,
        'max_walltime_hours': 36,
        'node_pool': 'main',
        'dedicated_to': 'general',
        'nodes': [f'mnode{i:03d}' for i in range(1, 97)],
        'from_route_only': True,
    },
    'longq': {
        'type': 'Execution',
        'route_via': 'entryq',
        'priority': 10,
        'max_walltime_hours': 168,
        'node_pool': 'main',
        'dedicated_to': 'general',
        'nodes': [f'mnode{i:03d}' for i in range(1, 97)],
        'from_route_only': True,
    },
    'testq': {
        'type': 'Execution',
        'route_via': 'testq',
        'priority': 125,
        'max_walltime_hours': 4,
        'node_pool': 'hybrid',
        'dedicated_to': 'testing',
        'nodes': ['mnode097', 'mnode098', 'mnode099', 'mnode100', 'mnode101',
                  'mnode102', 'mnode103', 'mnode104', 'mnode105', 'mnode106',
                  'mfatnode001', 'mfatnode002', 'mfatnode003'],
        'from_route_only': False,
    },
}


def parse_qstat_q_output(text: str) -> Dict[str, Dict[str, int]]:
    """Parse qstat -q text into per-queue running and queued counts."""
    queues = {}
    for line in text.strip().splitlines():
        parts = line.split()
        if len(parts) >= 6 and parts[0] in KNOWN_QUEUES:
            qname = parts[0]
            try:
                # Format: Queue Memory CPU Time Walltime Node Run Que Lm State
                # In standard PBS output: Run is column 5 or 6, Que is next
                run_cnt = int(parts[-4])
                que_cnt = int(parts[-3])
                queues[qname] = {'running': run_cnt, 'queued': que_cnt}
            except (ValueError, IndexError):
                pass
    return queues


def score_queue(
    queue_name: str,
    requested_walltime_hours: float,
    requested_cpus: int,
    queue_telemetry: Dict[str, Dict[str, int]],
    node_idle_cpus: Dict[str, int] | None = None,
    allow_general_pool: bool = True,
    penalize_pool_saturation: bool = False,
) -> Tuple[float, str, str]:
    """Compute heuristic dispatch score for a candidate queue.

    Score formulation (HEURISTIC_RECOMMENDATION_ONLY):
        Score = Priority - (10.0 * queued_jobs) + (1.5 * idle_cpus) - (saturation_penalty if enabled)

    Returns:
        (score, recommended_submission_queue, explanation)
    """
    if queue_name not in KNOWN_QUEUES:
        return -1e9, '', f'Unknown queue: {queue_name}'

    qinfo = KNOWN_QUEUES[queue_name]
    sub_queue = qinfo['route_via']

    # Filter by general pool authorization
    if qinfo['dedicated_to'] == 'general' and not allow_general_pool:
        return -1e9, sub_queue, f'General cluster pool disabled by policy'

    # Filter by requested walltime
    if requested_walltime_hours > qinfo['max_walltime_hours']:
        return -1e9, sub_queue, (
            f"Walltime {requested_walltime_hours}h exceeds max "
            f"{qinfo['max_walltime_hours']}h"
        )

    # Base priority
    priority = qinfo['priority']

    # Telemetry
    telem = queue_telemetry.get(queue_name, {'running': 0, 'queued': 0})
    queued = telem['queued']
    running = telem['running']

    # Idle CPU bonus for the queue's node pool
    idle_cpus = 0
    if node_idle_cpus and qinfo['node_pool'] in node_idle_cpus:
        idle_cpus = node_idle_cpus[qinfo['node_pool']]

    # Scoring weights
    penalty_per_queued = 10.0
    bonus_per_idle_cpu = 1.5

    # Optional saturation penalty for cross-pool de-biasing
    saturation_penalty = 0.0
    if penalize_pool_saturation and idle_cpus == 0 and queued > 0:
        saturation_penalty = 500.0

    score = priority - (penalty_per_queued * queued) + (bonus_per_idle_cpu * idle_cpus) - saturation_penalty

    explanation = (
        f"Priority={priority}, Queued={queued} (penalty -{penalty_per_queued*queued:.0f}), "
        f"Running={running}, IdlePoolCPUs={idle_cpus} (bonus +{bonus_per_idle_cpu*idle_cpus:.0f}), "
        f"Dedicated={qinfo['dedicated_to']}"
    )
    if saturation_penalty > 0:
        explanation += f" (saturation penalty -{saturation_penalty:.0f})"
    return score, sub_queue, explanation


def select_best_queue(
    requested_walltime_hours: float = 1.0,
    requested_cpus: int = 1,
    queue_telemetry: Dict[str, Dict[str, int]] | None = None,
    node_idle_cpus: Dict[str, int] | None = None,
    allow_general_pool: bool = True,
    prefer_dedicated_hardware: bool = True,
    penalize_pool_saturation: bool = False,
) -> Dict[str, Any]:
    """Select the optimal submission queue across all candidate queues.

    Returns dictionary with selected queue, ranking list, dispatch forecast,
    and classification marked as HEURISTIC_RECOMMENDATION_ONLY.
    """
    if queue_telemetry is None:
        # Default snapshot matching current live observation
        queue_telemetry = {
            'normal_imfdfkmq': {'running': 10, 'queued': 2},
            'short_imfdfkmq': {'running': 0, 'queued': 0},
            'shortq': {'running': 9, 'queued': 83},
            'mediumq': {'running': 5, 'queued': 11},
            'longq': {'running': 198, 'queued': 402},
            'testq': {'running': 0, 'queued': 0},
        }

    if node_idle_cpus is None:
        node_idle_cpus = {
            'extension2': 0,    # 10 nodes x 16 cpus = 160 cpus, 100% full
            'main': 240,        # ~6 nodes free x 40 cpus = 240 idle
            'hybrid': 0,
        }

    rankings = []
    for qname in KNOWN_QUEUES:
        score, sub_queue, expl = score_queue(
            queue_name=qname,
            requested_walltime_hours=requested_walltime_hours,
            requested_cpus=requested_cpus,
            queue_telemetry=queue_telemetry,
            node_idle_cpus=node_idle_cpus,
            allow_general_pool=allow_general_pool,
            penalize_pool_saturation=penalize_pool_saturation,
        )

        # Dedicated hardware preference bonus
        effective_score = score
        if prefer_dedicated_hardware and KNOWN_QUEUES[qname]['dedicated_to'] == 'IMFD-FKM':
            effective_score += 50.0  # Stable IMFD environment bonus

        qinfo = KNOWN_QUEUES[qname]
        pool_idle = node_idle_cpus.get(qinfo['node_pool'], 0) if node_idle_cpus else 0
        pool_sat = (pool_idle == 0)
        q_telem = queue_telemetry.get(qname, {'running': 0, 'queued': 0})
        if pool_sat and q_telem['queued'] > 0:
            dispatch_f = DISPATCH_FORECAST_UNDETERMINED
        elif pool_idle >= requested_cpus and q_telem['queued'] == 0:
            dispatch_f = DISPATCH_FORECAST_IMMEDIATE
        else:
            dispatch_f = DISPATCH_FORECAST_QUEUED

        rankings.append({
            'execution_queue': qname,
            'submission_queue': sub_queue,
            'raw_score': score,
            'effective_score': effective_score,
            'feasible': score > -1e8,
            'explanation': expl,
            'dedicated_to': KNOWN_QUEUES[qname]['dedicated_to'],
            'node_pool': qinfo['node_pool'],
            'pool_idle_cpus': pool_idle,
            'pool_saturated': pool_sat,
            'dispatch_forecast': dispatch_f,
        })

    rankings.sort(key=lambda x: x['effective_score'], reverse=True)
    winner = rankings[0]

    winner_qinfo = KNOWN_QUEUES[winner['execution_queue']]
    winner_pool_idle = node_idle_cpus.get(winner_qinfo['node_pool'], 0) if node_idle_cpus else 0
    winner_telem = queue_telemetry.get(winner['execution_queue'], {'running': 0, 'queued': 0})
    if winner_pool_idle == 0 and winner_telem['queued'] > 0:
        overall_forecast = DISPATCH_FORECAST_UNDETERMINED
    elif winner_pool_idle >= requested_cpus and winner_telem['queued'] == 0:
        overall_forecast = DISPATCH_FORECAST_IMMEDIATE
    else:
        overall_forecast = DISPATCH_FORECAST_QUEUED

    return {
        'classification': CLASSIFICATION,
        'selected_submission_queue': winner['submission_queue'],
        'selected_execution_queue': winner['execution_queue'],
        'effective_score': winner['effective_score'],
        'dispatch_forecast': overall_forecast,
        'cross_pool_bias_warning': (
            'Static PBS queue priority is an intra-pool ranking metric. '
            'Across disjoint node pools (extension2 vs main), dispatch latency depends on unobservable '
            'remaining walltimes of running jobs (query_other_jobs=False) and is EARLIEST_START_UNDETERMINED '
            'when the pool is saturated.'
        ),
        'explanation': winner['explanation'],
        'rankings': rankings,
    }


def main():
    parser = argparse.ArgumentParser(description='Mode-I Intelligent PBS Queue Selector (HEURISTIC_RECOMMENDATION_ONLY)')
    parser.add_argument('--walltime', type=float, default=1.0, help='Requested walltime in hours')
    parser.add_argument('--cpus', type=int, default=1, help='Requested CPUs')
    parser.add_argument('--disallow-general', action='store_true', help='Disallow general pool queues')
    parser.add_argument('--penalize-saturation', action='store_true', help='Apply pool saturation penalty for cross-pool de-biasing')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    args = parser.parse_args()

    result = select_best_queue(
        requested_walltime_hours=args.walltime,
        requested_cpus=args.cpus,
        allow_general_pool=not args.disallow_general,
        penalize_pool_saturation=args.penalize_saturation,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Classification:           {result['classification']}")
        print(f"Optimal Submission Queue: {result['selected_submission_queue']}")
        print(f"Target Execution Queue:   {result['selected_execution_queue']}")
        print(f"Effective Score:          {result['effective_score']:.1f}")
        print(f"Dispatch Forecast:        {result['dispatch_forecast']}")
        print(f"Details:                  {result['explanation']}")
        print(f"Cross-Pool Note:          {result['cross_pool_bias_warning']}")
        print("\nQueue Ranking Hierarchy:")
        for i, r in enumerate(result['rankings'], 1):
            status = 'FEASIBLE' if r['feasible'] else 'DISQUALIFIED'
            print(f"  {i}. {r['execution_queue']:<16} -> {r['submission_queue']:<16} [Score: {r['effective_score']:>7.1f}] ({status}, forecast: {r['dispatch_forecast']})")


if __name__ == '__main__':
    main()
