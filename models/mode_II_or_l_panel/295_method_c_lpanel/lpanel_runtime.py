"""
models/mode_II_or_l_panel/295_method_c_lpanel/lpanel_runtime.py
==============================================================
Bounded local L-Panel benchmark runner using the unchanged frozen UEL.

This runner reuses Case 1's transfer implementation unchanged. A two-step job
is audited after completion; a failed transfer gate forbids donor acceptance
and further cycles.
"""
from __future__ import print_function, division
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


import numpy as np
from scipy.spatial import cKDTree

QUAD_GP_LOCAL = [
    (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
    (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
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


def load_transfer():
    return transfer_state_fields


def connected_tip(nodes, elements, damage, threshold=0.90):
    """
    Find the damaged component attached to the re-entrant corner (250, 250),
    without path seeding.
    """
    for thr in (threshold, 0.80, 0.70, 0.50):
        active = {n for n in nodes if damage.get(n, 0.0) >= thr}
        if not active:
            continue
        graph = {n: set() for n in active}
        for conn in elements.values():
            selected = [n for n in conn if n in active]
            for n in selected:
                graph[n].update(selected)
        # Seed region: within 25 mm of re-entrant corner (250, 250)
        seen = {n for n in active if math.hypot(nodes[n][0] - 250.0, nodes[n][1] - 250.0) <= 25.0}
        todo = list(seen)
        while todo:
            curr = todo.pop()
            for n in graph[curr] - seen:
                seen.add(n)
                todo.append(n)
        if seen:
            tip = max(seen, key=lambda n: math.hypot(nodes[n][0] - 250.0, nodes[n][1] - 250.0))
            boundary = any(nodes[n][0] <= 5.0 for n in seen)
            return nodes[tip], boundary
    return (250.0, 250.0), False


def completion(peak, force, boundary, tip_x):
    if peak > 0 and abs(force) / peak < 0.05:
        return True, 'REACTION_FORCE_BELOW_5PCT_PEAK'
    if boundary or tip_x <= 5.0:
        return True, 'CONNECTED_DAMAGE_REACHED_LEFT_BOUNDARY'
    return False, 'IN_PROGRESS'


def geometry_audit(nodes, elements):
    """Actual signed Jacobians at quadrature points; never a hardcoded PASS."""
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
                dx = [-(1 - eta) / 4, (1 - eta) / 4, (1 + eta) / 4, -(1 + eta) / 4]
                dy = [-(1 - xi) / 4, -(1 + xi) / 4, (1 + xi) / 4, (1 - xi) / 4]
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
    """Reject a semantically wrong deck even when Abaqus datacheck accepts it."""
    lines = Path(path).read_text().splitlines()
    cards = []
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('*UEL PROPERTY'):
            cards.append([float(v) for v in lines[i + 1].split(',') if v.strip()])
    expected = [3.125, 9.5e-5, 25.84, 0.18, 1e-7, float(nphys)]
    if not cards or any(len(c) != 6 or any(not math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-12)
                                         for x, y in zip(c, expected)) for c in cards):
        raise ValueError('UEL properties must match frozen source order l0,Gc,E,nu,k,N_PHYS: ' + str(cards))


def write_json(path, value):
    temp = Path(str(path) + '.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temp, path)


def ensure_fortran_env():
    """Ensure Intel oneAPI Fortran compiler (ifx) and MSVC are in PATH on Windows."""
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
    def __init__(self, api, run_dir, cpus=4, max_cycles=7, donor_checkpoint=None, publish_dir=None):
        self.api = api
        self.run = Path(run_dir).resolve()
        self.run.mkdir(parents=True, exist_ok=True)
        self.publish_dir = Path(publish_dir).resolve() if publish_dir else (HERE / 'local_windows_adaptive_run')
        self.cpus = cpus
        self.max_cycles = max_cycles
        ensure_fortran_env()
        self.abaqus = shutil.which('abaqus') or r'C:\SIMULIA\Commands\abaqus.bat'
        self.transfer = load_transfer()
        self.watch = api.StallWatchdog()
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
        # Extract companion UMAT fields (SDV1=damage, SDV2=history, SDV17/18=energies, U, RF)
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
        return json.loads(target.read_text())

    def plot(self, job, mesh, fields, summary):
        import matplotlib
        matplotlib.use('Agg')
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
        fig, (a, b) = plt.subplots(1, 2, figsize=(12, 6.0), layout='constrained')
        a.add_collection(PolyCollection(polygons, facecolors='white', edgecolors='#435568', linewidths=0.15))
        a.set_title('Physical Mesh | %d elements (%d quads, %d tris)' % (
            len(polygons), len(quads), len(tris)
        ), fontsize=10)
        im = b.tripcolor(Triangulation(xy[:, 0], xy[:, 1], np.array(triangles)), d, cmap='inferno', vmin=0, vmax=1, shading='gouraud')
        b.set_title('Spatial Damage d (Averaged Companion SDV1)', fontsize=10)
        fig.colorbar(im, ax=b, label='Phase-Field Damage d')
        for ax in (a, b):
            ax.set(xlim=(-15.0, 515.0), ylim=(-15.0, 515.0), xlabel='x [mm]', ylabel='y [mm]')
            ax.set_aspect('equal')
        fig.suptitle('Method C L-Panel Benchmark | Cycle %d | uy=%.6f mm | Peak RF2=%.4f kN\nStatus: %s' % (
            summary['cycle'], summary['terminal_uy_mm'], summary['peak_rf2_kn'], summary['status']
        ), fontsize=11)
        image = self.run / (job + '_mesh_damage.png')
        fig.savefig(image, dpi=180)
        plt.close(fig)
        return image

    def publish(self, job, summary, mesh, image):
        folder = self.publish_dir
        folder.mkdir(parents=True, exist_ok=True)
        files = []
        for path in (self.run / (job + '_SUMMARY.json'), self.run / (job + '.sta'),
                     self.run / (job + '.dat'), self.run / (job + '.inp'),
                     self.run / (job + '_checkpoint.json'), mesh, image):
            dest = folder / path.name
            shutil.copy2(path, dest)
            files.append(str(dest.relative_to(ROOT)))
        index = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT, stdin=subprocess.DEVNULL)
        if index.returncode:
            raise RuntimeError('Pre-existing staged changes preserved; reconcile before evidence commit')
        subprocess.run(['git', 'add', '-f', '--'] + files, cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
        subprocess.run(['git', 'commit', '-m', 'feat(lpanel): record audited dynamic L-panel benchmark cycle ' + str(summary['cycle'])],
                       cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, stdin=subprocess.DEVNULL, text=True).strip()
        relative = str((folder / image.name).relative_to(ROOT)).replace('\\', '/')
        subprocess.run(['git', 'cat-file', '-e', commit + ':' + relative], cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
        manifest = folder / 'image_manifest.json'
        entries = json.loads(manifest.read_text()) if manifest.exists() else []
        entries = [e for e in entries if e.get('cycle') != summary['cycle']]
        entries.append({
            'cycle': summary['cycle'],
            'uy_mm': summary['terminal_uy_mm'],
            'path': relative,
            'commit': commit,
            'image_sha256': self.api.compute_sha256(image),
            'url': 'https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/' + commit + '/' + relative,
            'mesh_sha256': summary['mesh_sha256'],
            'source_sha256': summary['source_sha256']
        })
        entries.sort(key=lambda e: e['cycle'])
        write_json(manifest, entries)
        subprocess.run(['git', 'add', '--', str(manifest.relative_to(ROOT))], cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
        subprocess.run(['git', 'commit', '-m', 'docs(lpanel): pin dynamic cycle %d image provenance' % summary['cycle']], cwd=ROOT, stdin=subprocess.DEVNULL, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, stdin=subprocess.DEVNULL, check=True, timeout=120)
        self.watch.record_agent_progress()

    def execute(self):
        lock = self.run / 'execution_state.json'
        if lock.exists():
            if self.donor_checkpoint:
                lock.unlink()
            else:
                raise RuntimeError('Existing run requires checkpoint reconciliation, never an automatic retry: ' + str(lock))
        write_json(lock, {'active': True, 'pid': os.getpid(), 'started_at': time.time(), 'max_cycles': self.max_cycles,
                          'cpus': self.cpus, 'pbs_submissions': 0, 'benchmark': 'L-Shaped Panel (Winkler 2001 / Miehe 2010)'})
        source = ROOT / 'models/pandey_kumar_mode1/f42_mixed_uel.for'
        if self.api.compute_sha256(source) != self.api.FROZEN_UEL_SHA256:
            raise RuntimeError('Frozen source mismatch: ' + source.name)
        shutil.copy2(source, self.run / source.name)
        donor = None
        donor_mesh = None
        first_cycle = 0

        if self.donor_checkpoint:
            checkpoint = json.loads(self.donor_checkpoint.read_text())
            previous = checkpoint['summary']
            phys = Path(checkpoint['mesh_path'])
            previous_input = Path(checkpoint['odb_path']).with_suffix('.inp')
            sta = Path(checkpoint['odb_path']).with_suffix('.sta')
            if not phys.exists() and (self.donor_checkpoint.parent / phys.name).exists():
                phys = self.donor_checkpoint.parent / phys.name
            if not previous_input.exists() and (self.donor_checkpoint.parent / previous_input.name).exists():
                previous_input = self.donor_checkpoint.parent / previous_input.name
            if not sta.exists() and (self.donor_checkpoint.parent / sta.name).exists():
                sta = self.donor_checkpoint.parent / sta.name
            if (previous['source_sha256'] != self.api.FROZEN_UEL_SHA256 or
                previous['status'] != 'CONVERGED_AUDITED' or
                self.api.compute_sha256(phys) != previous['mesh_sha256'] or
                self.api.compute_sha256(previous_input) != previous['input_sha256'] or
                'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta.read_text(errors='replace')):
                raise RuntimeError('Donor evidence, hash or convergence mismatch; refusing resume')
            donor = checkpoint['fields']['terminal']
            donor_mesh = self.api.parse_physical_mesh(str(phys))
            self.peak = previous['peak_rf2_kn']
            self.tips = checkpoint.get('tip_history', [previous['tip_mm']] if previous['cycle'] == 0 else [])
            if not self.tips:
                raise RuntimeError('Historical tip path missing; cannot invent resumed arc length')
            first_cycle = previous['cycle'] + 1
            write_json(self.run / 'donor_receipt.json', {
                'checkpoint': str(self.donor_checkpoint),
                'sha256': self.api.compute_sha256(self.donor_checkpoint),
                'cycle': previous['cycle'],
                'cutoff': {'increment': donor['step_frame'], 'frame_time': donor['frame_time']}
            })

        if first_cycle > self.max_cycles:
            raise ValueError('Cycle cap precedes the supplied donor; no run started')

        for cycle in range(first_cycle, self.max_cycles + 1):
            stalled, reason, details = self.watch.check_agent_stall()
            if stalled:
                raise RuntimeError('Agent progress guard: ' + reason + '; ' + details)
            job = 'PK_METHOD_C_LPANEL_COARSE_JOB1' if cycle == 0 else 'PK_METHOD_C_LPANEL_CYCLE%d' % cycle
            inp = self.run / (job + '.inp')
            phys = self.run / (job + '_PHYS.inp')

            if cycle == 0:
                self.command([self.abaqus, 'cae', 'noGUI=' + str(HERE / 'generate_lpanel_adaptive_corridor_mesh.py'),
                              '--', str(phys), '250.0', '250.0'], job + '_coarse_mesh', timeout=600)
                mesh = self.api.parse_physical_mesh(str(phys))
                nodes, quads, tris, _ = mesh
                self.api.assemble_lpanel_coupled_deck(
                    str(inp), nodes, quads, tris,
                    donor_uy=0.0, target_uy=self.api.DEFAULT_COARSE_UY_MM,
                    is_coarse=True
                )
            else:
                last_tip = self.tips[-1]
                self.command([self.abaqus, 'cae', 'noGUI=' + str(HERE / 'generate_lpanel_adaptive_corridor_mesh.py'),
                              '--', str(phys), str(last_tip[0]), str(last_tip[1])], job + '_mesh', timeout=600)
                if not phys.exists():
                    raise RuntimeError('Mesh generator did not create expected file: ' + str(phys))
                mesh = self.api.parse_physical_mesh(str(phys))
                nodes, quads, tris, _ = mesh

            if not nodes or not quads or len(quads) + len(tris) >= 35000:
                raise RuntimeError('Mesh missing or outside bounded element scope: %d elements' % (len(quads) + len(tris)))
            qa = geometry_audit(nodes, {**quads, **tris})
            if not qa['positive_jacobians_pass'] or not qa['edge_ratio_le_5_pass']:
                write_json(self.run / (job + '_mesh_audit.json'), qa)
                raise RuntimeError('Physical mesh Jacobian or edge ratio failed')

            from generate_lpanel_adaptive_corridor_mesh import evaluate_corridor_audit
            tip_eval_x = self.tips[-1][0] if cycle else 250.0
            tip_eval_y = self.tips[-1][1] if cycle else 250.0
            audit = evaluate_corridor_audit(nodes, {**quads, **tris},
                {**{e: 'QUAD' for e in quads}, **{e: 'TRI' for e in tris}},
                tip_x=tip_eval_x, tip_y=tip_eval_y)
            audit.update(qa)
            write_json(self.run / (job + '_mesh_audit.json'), audit)
            if not all(audit['gates'].values()):
                raise RuntimeError('Physical mesh quality audit failed')

            if cycle:
                dn, dq, dt, _ = donor_mesh
                d = {int(n): v for n, v in donor['damage'].items()}
                h = {tuple(map(int, k.split('_'))): v for k, v in donor['history'].items()}
                rd, rh = self.transfer(dn, dq, dt, d, h, nodes, quads, tris)
                target_uy = donor['uy'] + self.api.DEFAULT_LOAD_INCREMENT_MM
                self.api.assemble_lpanel_coupled_deck(
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
            tip, boundary = connected_tip(nodes, {**quads, **tris}, {int(n): v for n, v in terminal['damage'].items()})
            self.tips.append(tip)
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
            done, reason = completion(self.peak, terminal['rf2'], boundary, tip[0])

            summary = {
                'cycle': cycle,
                'job_name': job,
                'status': 'CONVERGED_AUDITED' if accepted else 'TRANSFER_GATE_FAILED',
                'benchmark': 'L-Shaped Panel (Winkler 2001 / Miehe 2010 Fig. 19)',
                'donor_uy_mm': donor['uy'] if cycle else 0.0,
                'terminal_uy_mm': terminal['uy'],
                'terminal_rf2_kn': terminal['rf2'],
                'peak_rf2_kn': self.peak,
                'tip_mm': tip,
                'tip_history_chord_sum_mm': self.api.compute_cumulative_crack_arc_length(self.tips),
                'max_damage': max_damage,
                'mesh_elements': len(quads) + len(tris),
                'mesh_nodes': len(nodes),
                'gate_results': gates,
                'elapsed_seconds': elapsed,
                'completion': done and accepted,
                'completion_reason': reason if accepted else 'TRANSFER_GATE_FAILED',
                'input_sha256': self.api.compute_sha256(inp),
                'mesh_sha256': self.api.compute_sha256(phys),
                'source_sha256': self.api.FROZEN_UEL_SHA256,
                'donor_cutoff': {'frame': donor['step_frame'], 'time': donor['frame_time']} if cycle else None,
                'pbs_submissions': 0,
                'cumulative_pbs_submissions': 73
            }
            summary['transfer_implementation_sha256'] = self.api.compute_sha256(HERE / 'lpanel_runtime.py')
            summary['transfer_implementation'] = 'cKDTree nearest-neighbour nodal damage and Gauss-point history transfer'
            summary['donor_checkpoint_sha256'] = self.api.compute_sha256(self.donor_checkpoint) if self.donor_checkpoint else None

            write_json(self.run / (job + '_SUMMARY.json'), summary)
            write_json(self.run / (job + '_checkpoint.json'), {
                'summary': summary,
                'fields': fields,
                'mesh_path': str(phys),
                'odb_path': str(self.run / (job + '.odb')),
                'tip_history': self.tips
            })
            image = self.plot(job, mesh, terminal, summary)
            self.publish(job, summary, phys, image)

            if not accepted:
                raise RuntimeError('Scientific transfer gate failed; preserved cycle requires independent review')
            if done:
                write_json(lock, {'active': False, 'completed': True, 'last_cycle': cycle, 'reason': reason})
                return summary

            self.donor_checkpoint = self.run / (job + '_checkpoint.json')
            donor, donor_mesh = terminal, mesh

        write_json(lock, {'active': False, 'completed': False, 'last_cycle': self.max_cycles,
                          'reason': 'COARSE_QUALIFICATION_COMPLETE' if self.max_cycles == 0 else
                          'BOUNDED_CYCLE_CAP_REACHED; independent review required'})
        return summary
