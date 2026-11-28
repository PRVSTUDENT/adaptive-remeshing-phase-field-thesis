# -*- coding: utf-8 -*-
"""
models/complex_two_hole/two_hole_runtime.py
===========================================
Task: METHOD-C-COMPLEX-MODELS
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-001

Bounded local runner for Problem 1 (Inclined Notch + Two Holes in Series):
- Step 1: Fixed-load re-equilibration hold (*STATIC\n1.0, 1.0, 1.0E-08, 1.0)
- Step 2: Forward crack propagation (*STATIC, RIKS)
- State transfer: cKDTree nearest-neighbor mapping of damage d and history H
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

import two_hole_single_job_orchestrator as orch
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
    Finds Crack 1 tip (connected to notch root) and Crack 2 tip (initiated from Hole 1 towards Hole 2).
    Returns: (tip1, crack1_entered_hole1), (tip2, crack2_entered_hole2)
    """
    root_x, root_y = orch.NOTCH_TIP_X, orch.NOTCH_TIP_Y
    tip1 = (root_x, root_y)
    c1_entered_h1 = False

    # 1. Crack 1 from notch root towards Hole 1
    for thr in (threshold, 0.80, 0.70, 0.50):
        active = {n for n in nodes if damage.get(n, 0.0) >= thr}
        if not active:
            continue
        graph = {n: set() for n in active}
        for conn in elements.values():
            selected = [n for n in conn if n in active]
            for n in selected:
                graph[n].update(selected)
        seen = {n for n in active if math.hypot(nodes[n][0] - root_x, nodes[n][1] - root_y) <= 0.05}
        todo = list(seen)
        while todo:
            curr = todo.pop()
            for n in graph[curr] - seen:
                seen.add(n)
                todo.append(n)
        if seen:
            best_n = max(seen, key=lambda n: math.hypot(nodes[n][0] - root_x, nodes[n][1] - root_y))
            tip1 = nodes[best_n]
            d_h1 = math.hypot(tip1[0] - orch.HOLE1_X, tip1[1] - orch.HOLE1_Y)
            if d_h1 <= orch.HOLE1_PENETRATION_DIST_MM:
                c1_entered_h1 = True
            break

    # 2. Crack 2 re-initiated from Hole 1 far side (x >= 0.70)
    tip2 = None
    c2_entered_h2 = False
    for thr in (threshold, 0.80, 0.70, 0.50):
        active2 = {n for n in nodes if damage.get(n, 0.0) >= thr and nodes[n][0] >= 0.70}
        if not active2:
            continue
        graph2 = {n: set() for n in active2}
        for conn in elements.values():
            selected = [n for n in conn if n in active2]
            for n in selected:
                graph2[n].update(selected)
        seen2 = {n for n in active2 if nodes[n][0] <= 0.76 and abs(nodes[n][1] - orch.HOLE1_Y) <= 0.08}
        todo2 = list(seen2)
        while todo2:
            curr = todo2.pop()
            for n in graph2[curr] - seen2:
                seen2.add(n)
                todo2.append(n)
        if seen2:
            best_n2 = max(seen2, key=lambda n: nodes[n][0])
            tip2 = nodes[best_n2]
            d_h2 = math.hypot(tip2[0] - orch.HOLE2_X, tip2[1] - orch.HOLE2_Y)
            if d_h2 <= orch.HOLE2_PENETRATION_DIST_MM:
                c2_entered_h2 = True
            break

    return (tip1, c1_entered_h1), (tip2, c2_entered_h2)


def completion(peak, force, tip1_info, tip2_info):
    """
    Evaluates Problem 1 completion criteria:
    - Primary: RF2 < 5% of peak.
    - Secondary: Crack 2 reaches Hole 2 boundary.
    - Tertiary: Any crack reaches plate outer boundary.
    """
    (tip1, c1_entered_h1) = tip1_info
    (tip2, c2_entered_h2) = tip2_info

    if peak > 0 and abs(force) / peak < 0.05:
        return True, 'REACTION_FORCE_BELOW_5PCT_PEAK'

    if c2_entered_h2 or (tip2 is not None and math.hypot(tip2[0] - orch.HOLE2_X, tip2[1] - orch.HOLE2_Y) <= orch.HOLE2_PENETRATION_DIST_MM):
        return True, 'CONNECTED_DAMAGE_ENTERED_HOLE2'

    for t in [tip1, tip2]:
        if t is not None:
            tx, ty = t
            if tx >= 0.98 or ty >= 0.98 or ty <= 0.02:
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
        self.tips = []
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

        # Add holes to plot
        theta = np.linspace(0, 2*np.pi, 100)
        h1_x = orch.HOLE1_X + orch.HOLE1_R * np.cos(theta)
        h1_y = orch.HOLE1_Y + orch.HOLE1_R * np.sin(theta)
        h2_x = orch.HOLE2_X + orch.HOLE2_R * np.cos(theta)
        h2_y = orch.HOLE2_Y + orch.HOLE2_R * np.sin(theta)
        for ax in (a, b):
            ax.plot(h1_x, h1_y, 'k-', lw=1.2)
            ax.plot(h2_x, h2_y, 'k-', lw=1.2)
            ax.plot([orch.NOTCH_START_X, orch.NOTCH_TIP_X], [orch.NOTCH_START_Y, orch.NOTCH_TIP_Y], 'k-', lw=2.0)
            ax.set(xlim=(-0.05, 1.05), ylim=(-0.05, 1.05), xlabel='x [mm]', ylabel='y [mm]')
            ax.set_aspect('equal')

        fig.suptitle('Method C Problem 1: Two Holes in Series | Cycle %d | uy=%.6f mm | Peak RF2=%.4f kN\nStatus: %s' % (
            summary['cycle'], summary['terminal_uy_mm'], summary['peak_rf2_kn'], summary['status']
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
            subprocess.run(['git', 'commit', '-m', f"feat(complex-p1): record audited Problem 1 cycle {summary['cycle']} evidence"],
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
                          'cpus': self.cpus, 'pbs_submissions': 0, 'benchmark': 'Problem 1: Inclined Notch + Two Holes in Series'})
        source = ROOT / 'models/pandey_kumar_mode1/f42_mixed_uel.for'
        if orch.compute_sha256(source) != orch.FROZEN_UEL_SHA256:
            raise RuntimeError('Frozen source mismatch: ' + source.name)
        shutil.copy2(source, self.run / source.name)
        donor = None
        donor_mesh = None
        first_cycle = 0

        if self.donor_checkpoint and self.donor_checkpoint.exists():
            checkpoint = json.loads(self.donor_checkpoint.read_text(encoding='utf-8'))
            previous = checkpoint['summary']
            phys = Path(checkpoint['mesh_path'])
            if not phys.exists() and (self.donor_checkpoint.parent / phys.name).exists():
                phys = self.donor_checkpoint.parent / phys.name
            donor = checkpoint['fields']['terminal']
            donor_mesh = orch.parse_physical_mesh(str(phys))
            self.peak = previous['peak_rf2_kn']
            self.tips = checkpoint.get('tip_history', [previous['active_tip_mm']] if previous.get('active_tip_mm') else [])
            first_cycle = previous['cycle'] + 1
            print(f"Resuming campaign from cycle {first_cycle} with donor {previous['job_name']}")

        for cycle in range(first_cycle, self.max_cycles + 1):
            stalled, reason, details = self.watch.check_agent_stall()
            if stalled:
                raise RuntimeError('Agent progress guard: ' + reason + '; ' + str(details))
            job = 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1' if cycle == 0 else 'PK_METHOD_C_TWO_HOLE_CYCLE%d' % cycle
            inp = self.run / (job + '.inp')
            phys = self.run / (job + '_PHYS.inp')

            mesh_gen_script = HERE / 'generate_two_hole_mesh.py'
            history_file = self.run / 'tip_history.json'
            write_json(history_file, self.tips)
            if cycle == 0:
                self.command([self.abaqus, 'cae', 'noGUI=' + str(mesh_gen_script),
                              '--', str(phys), str(orch.NOTCH_TIP_X), str(orch.NOTCH_TIP_Y),
                              '--history', str(history_file)], job + '_coarse_mesh', timeout=600)
                mesh = orch.parse_physical_mesh(str(phys))
                nodes, quads, tris, _ = mesh
                orch.assemble_two_hole_coupled_deck(
                    str(inp), nodes, quads, tris,
                    donor_uy=0.0, target_uy=orch.DEFAULT_COARSE_UY_MM,
                    is_coarse=True
                )
            else:
                last_tip = self.tips[-1]
                self.command([self.abaqus, 'cae', 'noGUI=' + str(mesh_gen_script),
                              '--', str(phys), str(last_tip[0]), str(last_tip[1]),
                              '--history', str(history_file)], job + '_mesh', timeout=600)
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

            from generate_two_hole_mesh import evaluate_corridor_audit
            tip_eval_x = self.tips[-1][0] if cycle else orch.NOTCH_TIP_X
            tip_eval_y = self.tips[-1][1] if cycle else orch.NOTCH_TIP_Y
            audit = evaluate_corridor_audit(nodes, {**quads, **tris},
                {**{e: 'QUAD' for e in quads}, **{e: 'TRI' for e in tris}},
                tip_x=tip_eval_x, tip_y=tip_eval_y, tip_history=self.tips)
            audit.update(qa)
            write_json(self.run / (job + '_mesh_audit.json'), audit)
            if not all(audit['gates'].values()):
                raise RuntimeError('Physical mesh quality audit failed: ' + str(audit['gates']))

            if cycle:
                dn, dq, dt, _ = donor_mesh
                d = {int(n): v for n, v in donor['damage'].items()}
                h = {tuple(map(int, k.split('_'))): v for k, v in donor['history'].items()}
                rd, rh = self.transfer(dn, dq, dt, d, h, nodes, quads, tris)
                target_uy = donor['uy'] + orch.DEFAULT_LOAD_INCREMENT_MM
                orch.assemble_two_hole_coupled_deck(
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
            tip1_info, tip2_info = connected_tips(nodes, {**quads, **tris}, damage_dict)
            active_tip = tip2_info[0] if (tip2_info[0] is not None) else tip1_info[0]
            if active_tip is not None:
                self.tips.append(list(active_tip))
            self.peak = max(self.peak, fields['peak_rf2'])
            max_damage = max(terminal['damage'].values())

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
            done, reason = completion(self.peak, terminal['rf2'], tip1_info, tip2_info)

            summary = {
                'cycle': cycle,
                'job_name': job,
                'status': 'CONVERGED_AUDITED' if accepted else 'TRANSFER_GATE_FAILED',
                'benchmark': 'Problem 1: Inclined Notch + Two Holes in Series',
                'donor_uy_mm': donor['uy'] if cycle else 0.0,
                'terminal_uy_mm': terminal['uy'],
                'terminal_rf2_kn': terminal['rf2'],
                'peak_rf2_kn': self.peak,
                'tip1_mm': list(tip1_info[0]) if tip1_info[0] else None,
                'tip2_mm': list(tip2_info[0]) if tip2_info[0] else None,
                'tip1_entered_hole1': tip1_info[1],
                'tip2_entered_hole2': tip2_info[1],
                'active_tip_mm': list(active_tip) if active_tip else None,
                'tip_history_chord_sum_mm': orch.compute_cumulative_crack_arc_length(self.tips),
                'max_damage': max_damage,
                'mesh_elements': len(quads) + len(tris),
                'mesh_nodes': len(nodes),
                'gate_results': gates,
                'elapsed_seconds': elapsed,
                'completion': done and accepted,
                'completion_reason': reason if accepted else 'TRANSFER_GATE_FAILED',
                'input_sha256': orch.compute_sha256(inp),
                'mesh_sha256': orch.compute_sha256(phys),
                'source_sha256': orch.FROZEN_UEL_SHA256,
                'donor_cutoff': {'frame': donor['step_frame'], 'time': donor['frame_time']} if cycle else None,
                'pbs_submissions': 0,
                'cumulative_pbs_submissions': 73
            }
            summary['transfer_implementation_sha256'] = orch.compute_sha256(HERE / 'two_hole_runtime.py')
            summary['transfer_implementation'] = 'cKDTree nearest-neighbour nodal damage and Gauss-point history transfer'

            write_json(self.run / (job + '_SUMMARY.json'), summary)
            checkpoint = {
                'summary': summary,
                'mesh_path': str(phys),
                'odb_path': str(self.run / (job + '.odb')),
                'fields': fields,
                'tip_history': self.tips
            }
            write_json(self.run / (job + '_checkpoint.json'), checkpoint)

            image = self.plot(job, mesh, terminal, summary)
            self.publish(job, summary, phys, image)

            print(f"Cycle {cycle} complete: RF2 = {terminal['rf2']:.4f} kN (Peak = {self.peak:.4f} kN) | Elements = {len(quads)+len(tris)} | Status = {reason}")

            if not accepted:
                raise RuntimeError('Transfer gate failed at cycle %d: force continuity %.4f%%' % (cycle, gates.get('force_continuity_delta_pct', 0.0)))

            if summary['completion']:
                print(f"\n=======================================================")
                print(f"Problem 1 Campaign COMPLETED at Cycle {cycle}!")
                print(f"Completion Reason: {summary['completion_reason']}")
                print(f"=======================================================\n")
                return summary

            donor = terminal
            donor_mesh = mesh

        return summary
