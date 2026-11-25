# -*- coding: utf-8 -*-
"""
models/complex_double_notch/double_notch_runtime.py
===================================================
Task: METHOD-C-COMPLEX-MODELS
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-004

Bounded local runner for Problem 2 (Double Notch Symmetrical Crack Coalescence):
- Step 1: Fixed-load re-equilibration hold (*STATIC\\n1.0, 1.0, 1.0E-08, 1.0)
- Step 2: Forward crack propagation (*STATIC, RIKS)
- State transfer: cKDTree nearest-neighbor mapping of damage d and history H
- Two-tip tracking & coalescence detection
- Periodic stall watchdog active
- Strictly 0 PBS submissions (cumulative count 73 preserved)
- Bitwise frozen UEL source CE8D5EDC... preserved
"""

from __future__ import print_function, division
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import numpy as np
from scipy.spatial import cKDTree

import double_notch_single_job_orchestrator as orch
from stall_watchdog import StallWatchdog

QUAD_GP_LOCAL = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    ( 1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    ( 1.0 / math.sqrt(3.0),  1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0),  1.0 / math.sqrt(3.0)),
]


def shape_functions_quad(xi, eta):
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta),
    ]


def compute_quad_gp_coords(elem_conn, node_coords):
    pts = [node_coords[nid] for nid in elem_conn]
    gp_coords = []
    for gp_idx, (xi, eta) in enumerate(QUAD_GP_LOCAL, start=1):
        N = shape_functions_quad(xi, eta)
        gx = sum(N[i] * pts[i][0] for i in range(4))
        gy = sum(N[i] * pts[i][1] for i in range(4))
        gp_coords.append((gp_idx, gx, gy))
    return gp_coords


def compute_tri_gp_coords(elem_conn, node_coords):
    pts = [node_coords[nid] for nid in elem_conn]
    gx = sum(p[0] for p in pts) / 3.0
    gy = sum(p[1] for p in pts) / 3.0
    return [(1, gx, gy)]


def transfer_state_fields(donor_nodes, donor_quads, donor_tris, donor_d, donor_h_gp,
                          recip_nodes, recip_quads, recip_tris):
    """
    State transfer of nodal damage d and Gauss-point history H using KD-tree
    nearest-neighbor interpolation without coordinate scale or bounding box limits.
    """
    # 1. Nodal damage transfer
    d_nids = sorted(donor_d.keys())
    donor_coords = np.array([donor_nodes[n] for n in d_nids], dtype=float)
    tree_d = cKDTree(donor_coords)

    r_nids = sorted(recip_nodes.keys())
    recip_coords = np.array([recip_nodes[n] for n in r_nids], dtype=float)
    _, d_idxs = tree_d.query(recip_coords)
    recip_d = {r_nids[i]: float(donor_d[d_nids[d_idxs[i]]]) for i in range(len(r_nids))}

    # 2. Gauss-point history transfer
    h_coords = []
    h_vals = []
    for eid, conn in donor_quads.items():
        if len(conn) == 4 and all(n in donor_nodes for n in conn):
            for gp_idx, gx, gy in compute_quad_gp_coords(conn, donor_nodes):
                h_coords.append((gx, gy))
                h_vals.append(donor_h_gp.get((eid, gp_idx), 0.0))

    for eid, conn in donor_tris.items():
        if len(conn) == 3 and all(n in donor_nodes for n in conn):
            for gp_idx, gx, gy in compute_tri_gp_coords(conn, donor_nodes):
                h_coords.append((gx, gy))
                h_vals.append(donor_h_gp.get((eid, gp_idx), 0.0))

    tree_h = cKDTree(np.array(h_coords, dtype=float))

    recip_h_gp = {}
    r_h_keys = []
    r_h_coords = []
    for eid, conn in recip_quads.items():
        if len(conn) == 4 and all(n in recip_nodes for n in conn):
            for gp_idx, gx, gy in compute_quad_gp_coords(conn, recip_nodes):
                r_h_keys.append((eid, gp_idx))
                r_h_coords.append((gx, gy))

    for eid, conn in recip_tris.items():
        if len(conn) == 3 and all(n in recip_nodes for n in conn):
            for gp_idx, gx, gy in compute_tri_gp_coords(conn, recip_nodes):
                r_h_keys.append((eid, gp_idx))
                r_h_coords.append((gx, gy))

    if r_h_coords:
        _, h_idxs = tree_h.query(np.array(r_h_coords, dtype=float))
        for i, key in enumerate(r_h_keys):
            recip_h_gp[key] = float(h_vals[h_idxs[i]])

    return recip_d, recip_h_gp


def connected_tips(nodes, elements, damage, threshold=0.90):
    """
    Two-tip tracker for Problem 2 (Double Notch):
    - Left tip: advances from Left Notch Tip (0.353553, 0.853553) rightward toward x=0.50.
    - Right tip: advances from Right Notch Tip (0.646447, 0.853553) leftward toward x=0.50.
    - Coalescence: True if connected damage joins Left root to Right root or tip distance <= 0.015 mm.
    Returns:
      tip1: (x, y) coordinates of Left crack tip
      tip2: (x, y) coordinates of Right crack tip
      coalesced: bool
    """
    root1_x, root1_y = orch.NOTCH1_TIP_X, orch.NOTCH1_TIP_Y
    root2_x, root2_y = orch.NOTCH2_TIP_X, orch.NOTCH2_TIP_Y

    tip1 = (root1_x, root1_y)
    tip2 = (root2_x, root2_y)
    coalesced = False

    for thr in (threshold, 0.80, 0.70, 0.50):
        active = {n for n in nodes if damage.get(n, 0.0) >= thr}
        if not active:
            continue

        graph = {n: set() for n in active}
        for conn in elements.values():
            selected = [n for n in conn if n in active]
            for n in selected:
                graph[n].update(selected)

        # 1. Left crack component from root1
        seen1 = {n for n in active if math.hypot(nodes[n][0] - root1_x, nodes[n][1] - root1_y) <= 0.05}
        todo1 = list(seen1)
        while todo1:
            curr = todo1.pop()
            for n in graph[curr] - seen1:
                seen1.add(n)
                todo1.append(n)

        # 2. Right crack component from root2
        seen2 = {n for n in active if math.hypot(nodes[n][0] - root2_x, nodes[n][1] - root2_y) <= 0.05}
        todo2 = list(seen2)
        while todo2:
            curr = todo2.pop()
            for n in graph[curr] - seen2:
                seen2.add(n)
                todo2.append(n)

        # Check if seen1 reaches root2 or seen1 and seen2 intersect
        if seen1 and seen2 and (seen1.intersection(seen2) or any(math.hypot(nodes[n][0] - root2_x, nodes[n][1] - root2_y) <= 0.05 for n in seen1)):
            coalesced = True

        if seen1:
            # Furthest advancing tip in +x direction into ligament (x >= root1_x)
            cand1 = [n for n in seen1 if nodes[n][0] >= root1_x - 1e-5]
            if cand1:
                best1 = max(cand1, key=lambda n: nodes[n][0])
                tip1 = nodes[best1]

        if seen2:
            # Furthest advancing tip in -x direction into ligament (x <= root2_x)
            cand2 = [n for n in seen2 if nodes[n][0] <= root2_x + 1e-5]
            if cand2:
                best2 = min(cand2, key=lambda n: nodes[n][0])
                tip2 = nodes[best2]

        if seen1 or seen2:
            break

    # Distance check for coalescence
    dist_tips = math.hypot(tip1[0] - tip2[0], tip1[1] - tip2[1])
    if dist_tips <= orch.COALESCENCE_DISTANCE_MM:
        coalesced = True

    return tip1, tip2, coalesced


def completion(peak, force, tip1, tip2, coalesced):
    """
    Evaluates Problem 2 completion criteria:
    - Primary: Coalescence (connected damage joins two cracks, or tips within 0.015 mm).
    - Secondary: Reaction force drop below 5% of peak.
    - Tertiary: Either crack reaches plate outer boundary.
    """
    if coalesced:
        return True, 'CONNECTED_DAMAGE_COALESCENCE'

    if peak > 0 and abs(force) / peak < 0.05:
        return True, 'REACTION_FORCE_BELOW_5PCT_PEAK'

    for t in [tip1, tip2]:
        if t is not None:
            tx, ty = t
            if tx <= 0.02 or tx >= 0.98 or ty <= 0.02 or ty >= 0.98:
                return True, 'CONNECTED_DAMAGE_REACHED_BOUNDARY'

    return False, 'IN_PROGRESS'


def geometry_audit(nodes, elements):
    determinants = []
    max_ratio = 0.0
    q = 1.0 / math.sqrt(3.0)
    for conn in elements.values():
        xy = [nodes[n] for n in conn]
        lengths = [math.dist(xy[i], xy[(i + 1) % len(xy)]) for i in range(len(xy))]
        max_ratio = max(max_ratio, max(lengths) / min(lengths) if min(lengths) > 0 else float('inf'))
        if len(conn) == 3:
            (x0, y0), (x1, y1), (x2, y2) = xy
            determinants.append((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))
        else:
            for xi, eta in [(-q, -q), (q, -q), (q, q), (-q, q)]:
                dx = [-(1 - eta) / 4.0, (1 - eta) / 4.0, (1 + eta) / 4.0, -(1 + eta) / 4.0]
                dy = [-(1 - xi) / 4.0, -(1 + xi) / 4.0, (1 + xi) / 4.0, (1 - xi) / 4.0]
                xx = sum(a * p[0] for a, p in zip(dx, xy))
                xy1 = sum(a * p[1] for a, p in zip(dx, xy))
                yx = sum(a * p[0] for a, p in zip(dy, xy))
                yy = sum(a * p[1] for a, p in zip(dy, xy))
                determinants.append(xx * yy - xy1 * yx)
    return {
        'minimum_quadrature_jacobian': min(determinants),
        'max_edge_length_ratio': max_ratio,
        'positive_jacobians_pass': min(determinants) > 0,
        'edge_ratio_le_5_pass': max_ratio <= 5.0
    }


def validate_uel_properties(path, nphys):
    lines = Path(path).read_text().splitlines()
    cards = []
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('*UEL PROPERTY'):
            cards.append([float(v) for v in lines[i + 1].split(',') if v.strip()])
    expected = [orch.BENCHMARK_L0_MM, orch.BENCHMARK_GC_KN_MM, orch.BENCHMARK_E_GPA,
                orch.BENCHMARK_NU, orch.BENCHMARK_K_RES, float(nphys)]
    if not cards or any(len(c) != 6 or any(not math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-12)
                                         for x, y in zip(c, expected)) for c in cards):
        raise ValueError('UEL properties must match frozen source order l0,Gc,E,nu,k,N_PHYS: ' + str(cards))


def write_json(path, value):
    temp = Path(str(path) + '.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temp, path)


def ensure_fortran_env():
    if shutil.which('ifx'):
        return
    vcvars = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat")
    setvars = Path(r"C:\Program Files (x86)\Intel\oneAPI\setvars.bat")
    if not vcvars.exists() or not setvars.exists():
        return
    cmd = f'call "{vcvars}" >nul 2>&1 && call "{setvars}" intel64 >nul 2>&1 && set'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ[k] = v


class LocalRunner:
    def __init__(self, run_dir, cpus=4, max_cycles=12, donor_checkpoint=None, publish_dir=None):
        self.run = Path(run_dir).resolve()
        self.run.mkdir(parents=True, exist_ok=True)
        self.publish_dir = Path(publish_dir).resolve() if publish_dir else (HERE / 'campaign_results')
        self.publish_dir.mkdir(parents=True, exist_ok=True)
        self.cpus = cpus
        self.max_cycles = max_cycles
        ensure_fortran_env()
        self.abaqus = shutil.which('abaqus') or r'C:\SIMULIA\Commands\abaqus.bat'
        self.transfer = transfer_state_fields
        self.watch = StallWatchdog()
        self.published = []
        self.peak = 0.0
        self.left_tips = []
        self.right_tips = []
        self.donor_checkpoint = Path(donor_checkpoint).resolve() if donor_checkpoint else None

    def command(self, args, name, solver=False, timeout=600):
        log = self.run / (name + '_command.log')
        if log.exists():
            log.unlink()
        started = time.time()
        if solver:
            self.watch.start_cycle()
        with log.open('w') as stream:
            p = subprocess.Popen(args, cwd=self.run, stdin=subprocess.DEVNULL,
                                 stdout=stream, stderr=subprocess.STDOUT)
            while p.poll() is None:
                time.sleep(5)
                if solver:
                    stalled, reason, details = self.watch.check_simulation_stall(str(self.run / (name + '.sta')))
                    if stalled:
                        write_json(self.run / (name + '_blocker.json'),
                                   {'reason': reason, 'details': details, 'pid': p.pid,
                                    'retry': False, 'master_goal_status': 'OPEN'})
                        subprocess.run([self.abaqus, 'terminate', 'job=' + name], cwd=self.run,
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=stream, timeout=30)
                        raise RuntimeError('Stall preserved; guarded bridge review required: ' + reason)
                elif time.time() - started > timeout:
                    p.terminate()
                    raise RuntimeError('Preparation subprocess timed out: ' + name)
        if p.returncode:
            raise RuntimeError('Command failed; preserved ' + str(log))
        return time.time() - started

    def extract(self, job):
        script = self.run / (job + '_extract.py')
        target = self.run / (job + '_fields.json')
        code = '''import odbAccess, json, sys
odb = odbAccess.openOdb(sys.argv[1], readOnly=True)
inst = list(odb.rootAssembly.instances.values())[0]
nphys = len(inst.elements) // 3
def state(frame):
    dgp = {}; hgp = {}; energies = {}
    for v in frame.fieldOutputs['SDV1'].values:
        dgp.setdefault((v.elementLabel - 1) % nphys + 1, []).append(float(v.data))
    for v in frame.fieldOutputs['SDV2'].values:
        hgp[str((v.elementLabel - 1) % nphys + 1) + '_' + str(v.integrationPoint)] = float(v.data)
    for key in ['SDV17', 'SDV18']:
        if key in frame.fieldOutputs:
            by = {}
            for v in frame.fieldOutputs[key].values:
                by[v.elementLabel] = float(v.data)
            energies[key] = sum(by.values())
    nd = {}
    for e in inst.elements:
        eid = (e.label - 1) % nphys + 1
        if eid in dgp:
            d = sum(dgp[eid]) / len(dgp[eid])
            for n in e.connectivity:
                nd.setdefault(n, []).append(d)
    damage = {str(n): sum(v) / len(v) for n, v in nd.items()}
    u_dict = {}
    if 'U' in frame.fieldOutputs:
        for v in frame.fieldOutputs['U'].values:
            if v.nodeLabel != 999999:
                u_dict[str(v.nodeLabel)] = [float(x) for x in v.data]
    def rp(key, comp=1):
        vals = [v for v in frame.fieldOutputs[key].values if v.nodeLabel == 999999]
        if not vals:
            raise ValueError('Missing RP ' + key)
        return float(vals[0].data[comp])
    return dict(damage=damage, history=hgp, displacements=u_dict, uy=rp('U', 1), rf2=rp('RF', 1),
                energies=energies, step_frame=frame.incrementNumber, frame_time=frame.frameValue)

steps = list(odb.steps.values())
result = {
    'hold': state(steps[0].frames[-1]),
    'terminal': state(steps[-1].frames[-1]),
    'steps': [s.name for s in steps]
}
result['peak_rf2'] = max(abs(float(v.data[1])) for s in steps for f in s.frames
                         for v in f.fieldOutputs['RF'].values if v.nodeLabel == 999999 and f.incrementNumber > 0)
with open(sys.argv[2], 'w') as f:
    json.dump(result, f)
odb.close()
'''
        script.write_text(code, encoding='utf-8')
        self.command([self.abaqus, 'python', str(script), str(self.run / (job + '.odb')), str(target)], job + '_extract', timeout=300)
        return json.loads(target.read_text(encoding='utf-8'))

    def plot(self, job, mesh, fields, summary):
        import matplotlib.pyplot as plt
        from matplotlib.collections import PolyCollection
        from matplotlib.tri import Triangulation
        import numpy as np
        nodes, quads, tris, _ = mesh
        ids = sorted(nodes)
        ix = {n: i for i, n in enumerate(ids)}
        xy = np.array([nodes[n] for n in ids])
        polygons = [xy[[ix[n] for n in e]] for e in list(quads.values()) + list(tris.values())]
        triangles = []
        for e in list(quads.values()) + list(tris.values()):
            q = [ix[n] for n in e]
            triangles.append(q[:3])
            if len(q) == 4:
                triangles.append([q[0], q[2], q[3]])
        d = [fields['damage'].get(str(n), 0.0) for n in ids]
        fig, (a, b) = plt.subplots(1, 2, figsize=(12, 5.5), layout='constrained')
        a.add_collection(PolyCollection(polygons, facecolors='white', edgecolors='#435568', linewidths=0.15))
        a.set_title('Physical Mesh | %d elements (%d quads, %d tris)' % (
            len(polygons), len(quads), len(tris)
        ), fontsize=10)
        im = b.tripcolor(Triangulation(xy[:, 0], xy[:, 1], np.array(triangles)), d, cmap='inferno', vmin=0, vmax=1, shading='gouraud')
        b.set_title('Spatial Damage d (Averaged Companion SDV1)', fontsize=10)
        fig.colorbar(im, ax=b, label='Phase-Field Damage d')

        # Add both notch seams to plot
        for ax in (a, b):
            # Left notch
            ax.plot([orch.NOTCH1_START_X, orch.NOTCH1_TIP_X],
                    [orch.NOTCH1_START_Y, orch.NOTCH1_TIP_Y], 'k-', lw=2.0)
            # Right notch
            ax.plot([orch.NOTCH2_START_X, orch.NOTCH2_TIP_X],
                    [orch.NOTCH2_START_Y, orch.NOTCH2_TIP_Y], 'k-', lw=2.0)
            ax.set(xlim=(-0.05, 1.05), ylim=(-0.05, 1.05), xlabel='x [mm]', ylabel='y [mm]')
            ax.set_aspect('equal')

        fig.suptitle('Method C Problem 2: Double Notch Symmetrical Plate | Cycle %d | uy=%.6f mm | Peak RF2=%.4f kN\nStatus: %s | Tip Dist: %.4f mm | Coalesced: %s' % (
            summary['cycle'], summary['terminal_uy_mm'], summary['peak_rf2_kn'], summary['status'],
            summary.get('tip_distance_mm', 0.0), summary.get('coalesced', False)
        ), fontsize=11)
        image = self.publish_dir / (job + '_mesh_damage.png')
        fig.savefig(image, dpi=180)
        plt.close(fig)
        return image

    def publish(self, job, summary, mesh_path, image):
        folder = self.publish_dir
        folder.mkdir(parents=True, exist_ok=True)
        files = []
        for path in (self.run / (job + '_SUMMARY.json'), self.run / (job + '.sta'),
                     self.run / (job + '.dat'), self.run / (job + '.inp'),
                     self.run / (job + '_checkpoint.json'), mesh_path, image):
            dest = folder / path.name
            if path != dest:
                shutil.copy2(path, dest)
            files.append(str(dest.relative_to(ROOT)))

        manifest = folder / 'image_manifest.json'
        entries = json.loads(manifest.read_text()) if manifest.exists() else []
        entries = [e for e in entries if e.get('cycle') != summary['cycle']]
        relative = str((folder / image.name).relative_to(ROOT)).replace('\\', '/')
        entries.append({
            'cycle': summary['cycle'],
            'uy_mm': summary['terminal_uy_mm'],
            'path': relative,
            'commit': 'PENDING',
            'image_sha256': orch.compute_sha256(image),
            'url': 'https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/main/' + relative,
            'mesh_sha256': summary['mesh_sha256'],
            'source_sha256': summary['source_sha256']
        })
        entries.sort(key=lambda e: e['cycle'])
        write_json(manifest, entries)
        files.append(str(manifest.relative_to(ROOT)))

        # Commit and push
        try:
            subprocess.run(['git', 'add', '-f', '--'] + files, cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
            subprocess.run(['git', 'commit', '-m', f"feat(complex-p2): record audited Problem 2 cycle {summary['cycle']} evidence"],
                           cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
            commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, stdin=subprocess.DEVNULL, text=True).strip()
            # Update commit SHA in manifest
            entries[-1]['commit'] = commit
            entries[-1]['url'] = f"https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/{commit}/{relative}"
            write_json(manifest, entries)
            subprocess.run(['git', 'add', '-f', '--', str(manifest.relative_to(ROOT))], cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
            subprocess.run(['git', 'commit', '--amend', '--no-edit'], cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, stdin=subprocess.DEVNULL, check=True, timeout=120)
        except Exception as e:
            print("Git commit/push warning:", e)

        self.watch.record_agent_progress()

    def execute(self):
        lock = self.run / 'execution_state.json'
        if lock.exists():
            if self.donor_checkpoint:
                lock.unlink()
            else:
                pass
        write_json(lock, {'active': True, 'pid': os.getpid(), 'started_at': time.time(), 'max_cycles': self.max_cycles,
                          'cpus': self.cpus, 'pbs_submissions': 0, 'benchmark': 'Problem 2: Double Notch Symmetrical Crack Coalescence'})
        source = ROOT / 'models/pandey_kumar_mode1/f42_mixed_uel.for'
        if orch.compute_sha256(source) != orch.FROZEN_UEL_SHA256:
            raise RuntimeError('Frozen source mismatch: ' + source.name)
        shutil.copy2(source, self.run / source.name)
        donor = None
        donor_mesh = None
        donor_checkpoint_sha256 = None
        first_cycle = 0

        if self.donor_checkpoint and self.donor_checkpoint.exists():
            checkpoint = json.loads(self.donor_checkpoint.read_text(encoding='utf-8'))
            donor_checkpoint_sha256 = orch.compute_sha256(self.donor_checkpoint)
            previous = checkpoint['summary']
            phys = Path(checkpoint['mesh_path'])
            if not phys.exists() and (self.donor_checkpoint.parent / phys.name).exists():
                phys = self.donor_checkpoint.parent / phys.name
            donor = checkpoint['fields']['terminal']
            donor_mesh = orch.parse_physical_mesh(str(phys))
            self.peak = previous['peak_rf2_kn']
            self.left_tips = checkpoint.get('left_tip_history', [previous['left_tip_mm']] if previous.get('left_tip_mm') else [])
            self.right_tips = checkpoint.get('right_tip_history', [previous['right_tip_mm']] if previous.get('right_tip_mm') else [])
            first_cycle = previous['cycle'] + 1
            print(f"Resuming campaign from cycle {first_cycle} with donor {previous['job_name']}")

        for cycle in range(first_cycle, self.max_cycles + 1):
            stalled, reason, details = self.watch.check_agent_stall()
            if stalled:
                raise RuntimeError('Agent progress guard: ' + reason + '; ' + str(details))
            job = 'PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1' if cycle == 0 else 'PK_METHOD_C_DOUBLE_NOTCH_CYCLE%d' % cycle
            inp = self.run / (job + '.inp')
            phys = self.run / (job + '_PHYS.inp')

            mesh_gen_script = HERE / 'generate_double_notch_mesh.py'
            hist1_file = self.run / 'tip1_history.json'
            hist2_file = self.run / 'tip2_history.json'
            write_json(hist1_file, self.left_tips)
            write_json(hist2_file, self.right_tips)

            if cycle == 0:
                self.command([self.abaqus, 'cae', 'noGUI=' + str(mesh_gen_script),
                              '--', str(phys),
                              str(orch.NOTCH1_TIP_X), str(orch.NOTCH1_TIP_Y),
                              str(orch.NOTCH2_TIP_X), str(orch.NOTCH2_TIP_Y),
                              '--history1', str(hist1_file),
                              '--history2', str(hist2_file)], job + '_coarse_mesh', timeout=600)
                mesh = orch.parse_physical_mesh(str(phys))
                nodes, quads, tris, _ = mesh
                orch.assemble_double_notch_coupled_deck(
                    str(inp), nodes, quads, tris,
                    donor_uy=0.0, target_uy=orch.DEFAULT_COARSE_UY_MM,
                    is_coarse=True
                )
            else:
                last_tip1 = self.left_tips[-1]
                last_tip2 = self.right_tips[-1]
                dist_now = math.hypot(last_tip2[0] - last_tip1[0], last_tip2[1] - last_tip1[1])
                
                # Check if donor mesh was already bridged across the entire coalescence ligament
                prev_bridged = False
                prev_mesh_path = None
                if self.donor_checkpoint and self.donor_checkpoint.exists():
                    try:
                        cp_data = json.loads(self.donor_checkpoint.read_text(encoding='utf-8'))
                        mp = Path(cp_data.get('mesh_path', ''))
                        if mp.exists():
                            prev_mesh_path = mp
                        elif (self.donor_checkpoint.parent / mp.name).exists():
                            prev_mesh_path = self.donor_checkpoint.parent / mp.name
                        
                        if prev_mesh_path and prev_mesh_path.exists():
                            audit_p = prev_mesh_path.parent / (prev_mesh_path.stem + '_audit.json')
                            if not audit_p.exists() and (self.run / (job + '_mesh_audit.json')).exists():
                                audit_p = self.run / (job + '_mesh_audit.json')
                            if audit_p.exists():
                                pa = json.loads(audit_p.read_text(encoding='utf-8'))
                                prev_bridged = pa.get('corridor_spec', {}).get('corridor_type') == 'DOUBLE_NOTCH_BRIDGED_NARROW_BAND'
                    except Exception:
                        prev_bridged = False

                # If donor already had bridged corridor spanning the entire ligament,
                # remeshing is not indicated (the entire propagation path is already uniformly refined).
                # Reuse donor physical mesh to avoid gratuitous non-matching interpolation errors.
                if dist_now <= 0.25 and prev_bridged and prev_mesh_path and prev_mesh_path.exists():
                    print(f"Cycle {cycle}: Ligament already bridged in donor mesh ({prev_mesh_path.name}). Reusing mesh.")
                    shutil.copy2(prev_mesh_path, phys)
                    mesh = orch.parse_physical_mesh(str(phys))
                    nodes, quads, tris, _ = mesh
                else:
                    self.command([self.abaqus, 'cae', 'noGUI=' + str(mesh_gen_script),
                                  '--', str(phys),
                                  str(last_tip1[0]), str(last_tip1[1]),
                                  str(last_tip2[0]), str(last_tip2[1]),
                                  '--history1', str(hist1_file),
                                  '--history2', str(hist2_file)], job + '_mesh', timeout=600)
                    if not phys.exists():
                        raise RuntimeError('Mesh generator did not create expected file: ' + str(phys))
                    mesh = orch.parse_physical_mesh(str(phys))
                    nodes, quads, tris, _ = mesh

            if not nodes or not quads or len(quads) + len(tris) >= 35000:
                raise RuntimeError('Mesh missing or outside bounded element scope: %d elements' % (len(quads) + len(tris)))
            qa = geometry_audit(nodes, {**quads, **tris})
            if not qa['positive_jacobians_pass'] or not qa['edge_ratio_le_5_pass']:
                write_json(self.run / (job + '_mesh_audit.json'), qa)
                raise RuntimeError('Physical mesh Jacobian or edge ratio failed')

            from generate_double_notch_mesh import evaluate_corridor_audit
            tip1_eval_x = self.left_tips[-1][0] if cycle and self.left_tips else orch.NOTCH1_TIP_X
            tip1_eval_y = self.left_tips[-1][1] if cycle and self.left_tips else orch.NOTCH1_TIP_Y
            tip2_eval_x = self.right_tips[-1][0] if cycle and self.right_tips else orch.NOTCH2_TIP_X
            tip2_eval_y = self.right_tips[-1][1] if cycle and self.right_tips else orch.NOTCH2_TIP_Y

            audit = evaluate_corridor_audit(nodes, {**quads, **tris},
                {**{e: 'QUAD' for e in quads}, **{e: 'TRI' for e in tris}},
                tip1_x=tip1_eval_x, tip1_y=tip1_eval_y, tip1_history=self.left_tips,
                tip2_x=tip2_eval_x, tip2_y=tip2_eval_y, tip2_history=self.right_tips)
            audit.update(qa)
            write_json(self.run / (job + '_mesh_audit.json'), audit)
            if not all(audit['gates'].values()):
                raise RuntimeError('Physical mesh quality audit failed: ' + str(audit['gates']))

            if cycle:
                dn, dq, dt, _ = donor_mesh
                d = {int(n): v for n, v in donor['damage'].items()}
                h = {tuple(map(int, k.split('_'))): v for k, v in donor['history'].items()}
                rd, rh = self.transfer(dn, dq, dt, d, h, nodes, quads, tris)
                load_inc = 0.00080 if cycle == 6 else (0.00030 if cycle == 5 else orch.DEFAULT_LOAD_INCREMENT_MM)
                target_uy = donor['uy'] + load_inc
                orch.assemble_double_notch_coupled_deck(
                    str(inp), nodes, quads, tris,
                    donor_uy=donor['uy'], target_uy=target_uy,
                    transferred_damage=rd, transferred_history=rh,
                    is_coarse=False, use_riks=True
                )

            validate_uel_properties(inp, len(quads) + len(tris))
            self.command([self.abaqus, 'job=' + job + '_DATACHECK', 'input=' + job, 'user=' + source.name,
                          'cpus=' + str(self.cpus), 'datacheck', 'interactive'], job + '_DATACHECK', timeout=600)
            elapsed = self.command([self.abaqus, 'job=' + job, 'input=' + job, 'user=' + source.name,
                                  'cpus=' + str(self.cpus), 'interactive'], job, solver=True)
            sta = self.run / (job + '.sta')
            if not sta.exists() or 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta.read_text(errors='replace'):
                raise RuntimeError('Solve incomplete; do not treat partial frame as completed cycle')

            fields = self.extract(job)
            terminal = fields['terminal']
            damage_dict = {int(n): v for n, v in terminal['damage'].items()}
            tip1, tip2, coalesced = connected_tips(nodes, {**quads, **tris}, damage_dict)

            if tip1 is not None:
                self.left_tips.append(list(tip1))
            if tip2 is not None:
                self.right_tips.append(list(tip2))

            self.peak = max(self.peak, fields['peak_rf2'])
            max_damage = max(terminal['damage'].values())
            dist_tips = math.hypot(tip1[0] - tip2[0], tip1[1] - tip2[1])

            s1 = orch.compute_individual_crack_arc_length(self.left_tips, root=(orch.NOTCH1_TIP_X, orch.NOTCH1_TIP_Y))
            s2 = orch.compute_individual_crack_arc_length(self.right_tips, root=(orch.NOTCH2_TIP_X, orch.NOTCH2_TIP_Y))

            gates = {}
            if cycle:
                if abs(donor['rf2']) < 1e-12:
                    raise RuntimeError('Cannot qualify relative force continuity against zero donor reaction')
                delta = 100.0 * (abs(fields['hold']['rf2']) - abs(donor['rf2'])) / abs(donor['rf2'])
                sdv17_donor = donor['energies'].get('SDV17', 0.0)
                sdv17_hold = fields['hold']['energies'].get('SDV17', 0.0)
                sdv18_donor = donor['energies'].get('SDV18', 0.0)
                sdv18_hold = fields['hold']['energies'].get('SDV18', 0.0)
                delta_sdv17 = 100.0 * (sdv17_hold - sdv17_donor) / sdv17_donor if sdv17_donor > 0 else 0.0
                delta_sdv18 = 100.0 * (sdv18_hold - sdv18_donor) / sdv18_donor if sdv18_donor > 0 else 0.0
                gates = {
                    'force_continuity_delta_pct': delta,
                    'force_continuity_pass': abs(delta) <= 5.0,
                    'energy_continuity_delta_sdv17_pct': delta_sdv17,
                    'energy_continuity_delta_sdv18_pct': delta_sdv18,
                    'global_max_damage_nonhealing_pass': max_damage >= max(donor['damage'].values()) - 1e-4,
                    'evaluation_timing': 'after two-step job; failure forbids donor acceptance and further cycles',
                    'hold_energies': fields['hold']['energies'],
                    'donor_energies': donor['energies']
                }

            accepted = not cycle or (gates['force_continuity_pass'] and gates['global_max_damage_nonhealing_pass'])
            done, reason = completion(self.peak, terminal['rf2'], tip1, tip2, coalesced)

            summary = {
                'cycle': cycle,
                'job_name': job,
                'status': 'CONVERGED_AUDITED' if accepted else 'TRANSFER_GATE_FAILED',
                'benchmark': 'Problem 2: Double Notch Symmetrical Crack Coalescence',
                'donor_uy_mm': donor['uy'] if cycle else 0.0,
                'terminal_uy_mm': terminal['uy'],
                'terminal_rf2_kn': terminal['rf2'],
                'peak_rf2_kn': self.peak,
                'left_tip_mm': list(tip1) if tip1 else None,
                'right_tip_mm': list(tip2) if tip2 else None,
                'tip_distance_mm': round(dist_tips, 6),
                'coalesced': coalesced,
                'left_crack_arc_length_s1_mm': s1,
                'right_crack_arc_length_s2_mm': s2,
                'max_damage': max_damage,
                'mesh_elements': len(quads) + len(tris),
                'mesh_nodes': len(nodes),
                'gate_results': gates,
                'elapsed_seconds': elapsed,
                'completion': done and accepted,
                'completion_reason': reason if accepted else 'TRANSFER_GATE_FAILED',
                'donor_checkpoint_sha256': donor_checkpoint_sha256,
                'input_sha256': orch.compute_sha256(inp),
                'mesh_sha256': orch.compute_sha256(phys),
                'source_sha256': orch.FROZEN_UEL_SHA256,
                'donor_cutoff': {'frame': donor['step_frame'], 'time': donor['frame_time']} if cycle else None,
                'pbs_submissions': 0,
                'cumulative_pbs_submissions': 73
            }
            summary['transfer_implementation_sha256'] = orch.compute_sha256(HERE / 'double_notch_runtime.py')
            summary['transfer_implementation'] = 'cKDTree nearest-neighbour nodal damage and Gauss-point history transfer'

            summary_path = self.run / (job + '_SUMMARY.json')
            write_json(summary_path, summary)

            checkpoint = {
                'summary': summary,
                'mesh_path': str(phys),
                'odb_path': str(self.run / (job + '.odb')),
                'fields': fields,
                'left_tip_history': self.left_tips,
                'right_tip_history': self.right_tips
            }
            checkpoint_path = self.run / (job + '_checkpoint.json')
            write_json(checkpoint_path, checkpoint)

            # Record checkpoint sha256 for the next cycle
            donor_checkpoint_sha256 = orch.compute_sha256(checkpoint_path)

            image = self.plot(job, mesh, terminal, summary)
            self.publish(job, summary, phys, image)

            print(f"Cycle {cycle} complete: RF2 = {terminal['rf2']:.4f} kN (Peak = {self.peak:.4f} kN) | Elements = {len(quads)+len(tris)} | Status = {reason} | Tip Dist = {dist_tips:.4f} mm | Coalesced = {coalesced}")

            if not accepted:
                raise RuntimeError('Transfer gate failed at cycle %d: force continuity %.4f%%' % (cycle, gates.get('force_continuity_delta_pct', 0.0)))

            if summary['completion']:
                print(f"\n=======================================================")
                print(f"Problem 2 Campaign COMPLETED at Cycle {cycle}!")
                print(f"Completion Reason: {summary['completion_reason']}")
                print(f"=======================================================\n")
                return summary

            donor = terminal
            donor_mesh = mesh

        return summary


def run_campaign(run_dir="models/complex_double_notch/run_campaign",
                 publish_dir="models/complex_double_notch/campaign_results",
                 cpus=4, max_cycles=12, donor_checkpoint=None):
    runner = LocalRunner(run_dir=run_dir, publish_dir=publish_dir, cpus=cpus,
                         max_cycles=max_cycles, donor_checkpoint=donor_checkpoint)
    return runner.execute()


if __name__ == "__main__":
    run_campaign()
