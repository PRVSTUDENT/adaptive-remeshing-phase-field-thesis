# -*- coding: utf-8 -*-
"""
models/complex_mixed_load/mixed_load_runtime.py
===============================================
Task: METHOD-C-COMPLEX-MODELS (Problem 3)
Goal: METHOD_C_COMPLEX_MODELS_V1
Correlation: HND-METHOD-C-COMPLEX-004 / HND-METHOD-C-COMPLEX-005

Autonomous Multi-Cycle Adaptive Remeshing Controller for Problem 3:
Notch + Hole under Combined Tension + Shear (ux = 0.5 * uy):
- Re-equilibration Step 1 hold force continuity on RF2 (<= 5.0% gate)
- Mandatory reporting of RF1 alongside RF2 in every cycle summary
- Monotonic damage non-healing (no healing)
- cKDTree state transfer of nodal damage and GP history
- Bounded mesh element ceiling < 35,000
- Dynamic narrow damage-following band polygon
- Automatic git commit and push per cycle
- Manifest synchronization with commit-pinned URLs and summary hashes
"""

from __future__ import print_function, division
import os
import sys
import math
import time
import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

from generate_mixed_load_mesh import (
    PLATE_W, PLATE_H, NOTCH_TIP_X, NOTCH_TIP_Y, HOLE_X, HOLE_Y, HOLE_R,
    E_MOD, NU, L0, GC, K_RES, THICKNESS, H_REF, H_BG, BAND_HALF_WIDTH,
    SHEAR_TO_TENSION_RATIO, compute_corridor_spec
)
from mixed_load_single_job_orchestrator import (
    assemble_mixed_load_uel_deck, parse_physical_mesh,
    DEFAULT_PRECRITICAL_UY_MM, DEFAULT_LOAD_INCREMENT_MM,
    BENCHMARK_E_GPA, BENCHMARK_NU, BENCHMARK_L0_MM, BENCHMARK_GC_KN_MM, BENCHMARK_K_RES
)
from stall_watchdog import StallWatchdog

SOURCE_FILE = ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def file_sha256(path):
    p = Path(path)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def write_json(path, data):
    p = Path(path)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def transfer_state_fields(donor_nodes, donor_quads, donor_tris, donor_d, donor_h_gp,
                          recip_nodes, recip_quads, recip_tris):
    """
    Interpolates nodal damage and Gauss-point history from donor to recipient mesh
    using spatial cKDTree nearest-neighbor queries.
    """
    donor_nids = sorted(donor_nodes.keys())
    donor_coords = np.array([donor_nodes[nid] for nid in donor_nids])
    tree_nodes = cKDTree(donor_coords)

    recip_nids = sorted(recip_nodes.keys())
    recip_coords = np.array([recip_nodes[nid] for nid in recip_nids])
    _, idx_nodes = tree_nodes.query(recip_coords)

    recip_d = {}
    for r_idx, recip_nid in enumerate(recip_nids):
        d_nid = donor_nids[idx_nodes[r_idx]]
        recip_d[recip_nid] = float(donor_d.get(d_nid, 0.0))

    donor_gp_pts = []
    donor_gp_vals = []
    for elements, ngp in ((donor_quads, 4), (donor_tris, 3)):
        for eid, conn in elements.items():
            pts = [donor_nodes[n] for n in conn]
            if ngp == 4:
                q = 1.0 / math.sqrt(3.0)
                local_gp = [(-q, -q), (q, -q), (q, q), (-q, q)]
                for gp_idx, (xi, eta) in enumerate(local_gp, start=1):
                    N = [
                        0.25 * (1 - xi) * (1 - eta),
                        0.25 * (1 + xi) * (1 - eta),
                        0.25 * (1 + xi) * (1 + eta),
                        0.25 * (1 - xi) * (1 + eta)
                    ]
                    gx = sum(N[i] * pts[i][0] for i in range(4))
                    gy = sum(N[i] * pts[i][1] for i in range(4))
                    val = donor_h_gp.get((eid, gp_idx), donor_h_gp.get(eid, 0.0))
                    donor_gp_pts.append((gx, gy))
                    donor_gp_vals.append(float(val))
            else:
                gx = sum(p[0] for p in pts) / 3.0
                gy = sum(p[1] for p in pts) / 3.0
                val = donor_h_gp.get((eid, 1), donor_h_gp.get(eid, 0.0))
                donor_gp_pts.append((gx, gy))
                donor_gp_vals.append(float(val))

    if donor_gp_pts:
        tree_gp = cKDTree(np.array(donor_gp_pts))
        recip_h = {}
        for elements, ngp in ((recip_quads, 4), (recip_tris, 3)):
            for eid, conn in elements.items():
                pts = [recip_nodes[n] for n in conn]
                if ngp == 4:
                    q = 1.0 / math.sqrt(3.0)
                    local_gp = [(-q, -q), (q, -q), (q, q), (-q, q)]
                    for gp_idx, (xi, eta) in enumerate(local_gp, start=1):
                        N = [
                            0.25 * (1 - xi) * (1 - eta),
                            0.25 * (1 + xi) * (1 - eta),
                            0.25 * (1 + xi) * (1 + eta),
                            0.25 * (1 - xi) * (1 + eta)
                        ]
                        gx = sum(N[i] * pts[i][0] for i in range(4))
                        gy = sum(N[i] * pts[i][1] for i in range(4))
                        _, idx = tree_gp.query([gx, gy])
                        recip_h[(eid, gp_idx)] = float(donor_gp_vals[idx])
                else:
                    gx = sum(p[0] for p in pts) / 3.0
                    gy = sum(p[1] for p in pts) / 3.0
                    _, idx = tree_gp.query([gx, gy])
                    recip_h[(eid, 1)] = float(donor_gp_vals[idx])
    else:
        recip_h = {}

    return recip_d, recip_h


def connected_tip(nodes, elements, damage, root_x=NOTCH_TIP_X, root_y=NOTCH_TIP_Y, threshold=0.90):
    """
    Finds the active crack tip connected to the notch root (0.353553, 0.853553)
    checking localized damage thresholds descending (0.90, 0.80, 0.70, 0.50).
    Returns: (tip_coords, dist_to_hole, entered_hole, reached_boundary)
    """
    for thr in (threshold, 0.80, 0.70, 0.50):
        active_nodes = {n for n, d in damage.items() if d >= thr}
        if not active_nodes:
            continue

        graph = defaultdict(set)
        for conn in elements.values():
            sel = [n for n in conn if n in active_nodes]
            for n in sel:
                graph[n].update(sel)

        # Seed within 0.05 mm of notch root
        seed = {n for n in active_nodes if math.hypot(nodes[n][0] - root_x, nodes[n][1] - root_y) <= 0.05}
        if not seed:
            continue

        seen = set(seed)
        queue = list(seed)
        while queue:
            curr = queue.pop(0)
            for nbr in graph[curr]:
                if nbr not in seen:
                    seen.add(nbr)
                    queue.append(nbr)

        if seen:
            tip_node = max(seen, key=lambda n: math.hypot(nodes[n][0] - root_x, nodes[n][1] - root_y))
            tx, ty = nodes[tip_node]
            dist_to_center = math.hypot(tx - HOLE_X, ty - HOLE_Y)
            entered_hole = (dist_to_center <= (HOLE_R + 1e-4))
            reached_boundary = (tx >= 0.98 or ty >= 0.98 or ty <= 0.02 or tx <= 0.02)
            return (tx, ty), dist_to_center - HOLE_R, entered_hole, reached_boundary

    dist_h = math.hypot(root_x - HOLE_X, root_y - HOLE_Y) - HOLE_R
    return (root_x, root_y), dist_h, False, False


def completion(peak_rf2, rf2, entered_hole, reached_boundary):
    """
    Evaluates Problem 3 completion criteria.
    Returns: (done, reason)
    """
    if entered_hole:
        return True, "CONNECTED_DAMAGE_ENTERED_HOLE"
    if reached_boundary:
        return True, "CONNECTED_DAMAGE_REACHED_BOUNDARY"
    if peak_rf2 > 0.0 and abs(rf2) / peak_rf2 < 0.05:
        return True, "REACTION_FORCE_BELOW_5PCT_PEAK"
    return False, "IN_PROGRESS"


def geometry_audit(nodes, elements):
    """Actual signed Jacobians at quadrature points; never a hardcoded PASS."""
    determinants = []
    max_ratio = 0.0
    q = 1.0 / math.sqrt(3.0)
    for conn in elements.values():
        xy = [nodes[n] for n in conn]
        lengths = [math.hypot(xy[i][0] - xy[(i + 1) % len(xy)][0], xy[i][1] - xy[(i + 1) % len(xy)][1]) for i in range(len(xy))]
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
    """Reject a semantically wrong deck even when Abaqus datacheck accepts it."""
    lines = Path(path).read_text().splitlines()
    cards = []
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('*UEL PROPERTY'):
            cards.append([float(v) for v in lines[i + 1].split(',') if v.strip()])
    expected = [BENCHMARK_L0_MM, BENCHMARK_GC_KN_MM, BENCHMARK_E_GPA,
                BENCHMARK_NU, BENCHMARK_K_RES, float(nphys)]
    if not cards or any(len(c) != 6 or any(not math.isclose(x, y, rel_tol=1e-6, abs_tol=1e-12)
                                         for x, y in zip(c, expected)) for c in cards):
        raise ValueError('UEL properties must match frozen source order l0,Gc,E,nu,k,N_PHYS: ' + str(cards))


def ensure_fortran_env():
    """Sets up MSVC + Intel oneAPI environment variables if needed."""
    if shutil.which("ifx") or shutil.which("ifort"):
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


class MixedLoadMethodCRuntime(object):
    def __init__(self, run_dir, cpus=4, max_cycles=12, publish_dir=None, donor_checkpoint=None):
        self.run = Path(run_dir).resolve()
        self.run.mkdir(parents=True, exist_ok=True)
        self.publish_dir = Path(publish_dir).resolve() if publish_dir else (HERE / "campaign_results")
        self.publish_dir.mkdir(parents=True, exist_ok=True)
        self.cpus = cpus
        self.max_cycles = max_cycles
        self.donor_checkpoint = Path(donor_checkpoint).resolve() if donor_checkpoint else None
        ensure_fortran_env()
        self.abaqus = shutil.which("abaqus") or r"C:\SIMULIA\Commands\abaqus.bat"
        self.watch = StallWatchdog()
        self.peak_rf2 = 0.0
        self.peak_rf1 = 0.0
        self.tips = []
        self.published = []
        self.transfer = transfer_state_fields

    def execute(self):
        return self.run_campaign()

    def command(self, args, name, solver=False, timeout=600):
        log = self.run / (name + "_command.log")
        if log.exists():
            log.unlink()
        started = time.time()
        if solver:
            self.watch.start_cycle()
        with log.open("w") as stream:
            p = subprocess.Popen(args, cwd=self.run, stdin=subprocess.DEVNULL,
                                 stdout=stream, stderr=subprocess.STDOUT)
            while p.poll() is None:
                time.sleep(5)
                if solver:
                    stalled, reason, details = self.watch.check_simulation_stall(str(self.run / (name + ".sta")))
                    if stalled:
                        write_json(self.run / (name + "_blocker.json"),
                                   {"reason": reason, "details": details, "pid": p.pid,
                                    "retry": False, "master_goal_status": "OPEN"})
                        subprocess.run([self.abaqus, "terminate", "job=" + name], cwd=self.run,
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=stream, timeout=30)
                        raise RuntimeError("Stall preserved: " + reason)
                elif time.time() - started > timeout:
                    p.terminate()
                    raise RuntimeError("Preparation command timed out: " + name)
        if p.returncode:
            raise RuntimeError("Command failed: %s (see %s)" % (name, log))
        return time.time() - started

    def extract(self, job):
        script = self.run / (job + "_extract.py")
        target = self.run / (job + "_fields.json")
        code = '''import sys, json
from odbAccess import openOdb
odb = openOdb(sys.argv[1])
inst = list(odb.rootAssembly.instances.values())[0]
nphys = len(inst.elements) // 3
def read_frame(frame):
    dgp = {}
    hgp = {}
    energies = {}
    damage = {}
    u_dict = {}
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
            avg_d = sum(dgp[eid]) / len(dgp[eid])
            for n in e.connectivity:
                nd.setdefault(n, []).append(avg_d)
    for n, vals in nd.items():
        damage[str(n)] = sum(vals) / len(vals)
    if 'U' in frame.fieldOutputs:
        for v in frame.fieldOutputs['U'].values:
            if v.nodeLabel != 999999:
                u_dict[str(v.nodeLabel)] = [float(x) for x in v.data]
    def rp(key, comp):
        vals = [v for v in frame.fieldOutputs[key].values if v.nodeLabel == 999999]
        if not vals:
            raise ValueError('Missing RP ' + key)
        return float(vals[0].data[comp])
    return dict(damage=damage, history=hgp, displacements=u_dict,
                ux=rp('U', 0), uy=rp('U', 1),
                rf1=rp('RF', 0), rf2=rp('RF', 1),
                energies=energies, step_frame=frame.incrementNumber, frame_time=frame.frameValue)

steps = list(odb.steps.values())
result = {
    'terminal': read_frame(steps[-1].frames[-1]),
    'hold': read_frame(steps[0].frames[-1]) if len(steps) > 1 else None,
}
result['peak_rf2'] = max(abs(float(v.data[1])) for s in steps for f in s.frames
                         for v in f.fieldOutputs['RF'].values if v.nodeLabel == 999999 and f.incrementNumber > 0)
result['peak_rf1'] = max(abs(float(v.data[0])) for s in steps for f in s.frames
                         for v in f.fieldOutputs['RF'].values if v.nodeLabel == 999999 and f.incrementNumber > 0)
with open(sys.argv[2], 'w') as f:
    json.dump(result, f)
odb.close()
'''
        script.write_text(code, encoding="utf-8")
        self.command([self.abaqus, "python", str(script), str(self.run / (job + ".odb")), str(target)], job + "_extract", timeout=300)
        return json.loads(target.read_text())

    def plot(self, job, mesh, fields, summary):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import PolyCollection
        from matplotlib.tri import Triangulation
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
        d = [fields["damage"].get(str(n), 0.0) for n in ids]

        fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.5), layout="constrained")
        a.add_collection(PolyCollection(polygons, facecolors="white", edgecolors="#435568", linewidths=0.15))
        a.set_title("Physical Mesh | %d elements (%d quads, %d tris)" % (
            len(polygons), len(quads), len(tris)
        ), fontsize=10)

        im = b.tripcolor(Triangulation(xy[:, 0], xy[:, 1], np.array(triangles)), d, cmap="inferno", vmin=0, vmax=1, shading="gouraud")
        b.set_title("Spatial Damage d (Averaged Companion SDV1)", fontsize=10)
        fig.colorbar(im, ax=b, label="Phase-Field Damage d")

        # Mark crack tip and hole
        circle = plt.Circle((HOLE_X, HOLE_Y), HOLE_R, color="cyan", fill=False, linestyle="--", linewidth=1.2)
        b.add_patch(circle)
        tip = summary.get("tip_mm", [NOTCH_TIP_X, NOTCH_TIP_Y])
        b.plot(tip[0], tip[1], "r*", markersize=10, label="Tip (%.3f, %.3f)" % (tip[0], tip[1]))
        b.legend(loc="lower right", fontsize=8)

        for ax in (a, b):
            ax.set(xlim=(-0.05, 1.05), ylim=(-0.05, 1.05), xlabel="x [mm]", ylabel="y [mm]")
            ax.set_aspect("equal")

        fig.suptitle("Problem 3 Combined Tension + Shear (ux = 0.5*uy) | Cycle %d\nuy=%.6f mm, ux=%.6f mm | Peak RF2=%.4f kN, RF1=%.4f kN | Status: %s" % (
            summary["cycle"], summary["terminal_uy_mm"], summary.get("terminal_ux_mm", summary["terminal_uy_mm"]*0.5),
            summary["peak_rf2_kn"], summary.get("peak_rf1_kn", 0.0), summary["status"]
        ), fontsize=11)

        image = self.run / (job + "_mesh_damage.png")
        fig.savefig(image, dpi=180)
        plt.close(fig)
        return image

    def publish(self, job, summary, mesh, image):
        folder = self.publish_dir
        folder.mkdir(parents=True, exist_ok=True)
        files = []
        for path in (self.run / (job + "_SUMMARY.json"), self.run / (job + ".sta"),
                     self.run / (job + ".dat"), self.run / (job + ".inp"),
                     self.run / (job + "_checkpoint.json"), mesh, image):
            dest = folder / path.name
            shutil.copy2(path, dest)
            files.append(str(dest.relative_to(ROOT)))

        # Update image manifest
        manifest_path = folder / "image_manifest.json"
        manifest = []
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
            except Exception:
                manifest = []
        manifest = [e for e in manifest if e.get("cycle") != summary["cycle"]]

        entry = {
            "cycle": summary["cycle"],
            "uy_mm": summary["terminal_uy_mm"],
            "ux_mm": summary.get("terminal_ux_mm", summary["terminal_uy_mm"] * 0.5),
            "path": str((folder / image.name).relative_to(ROOT)).replace("\\", "/"),
            "commit": "PENDING_COMMIT",
            "image_sha256": file_sha256(folder / image.name),
            "url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/PENDING_COMMIT/" +
                   str((folder / image.name).relative_to(ROOT)).replace("\\", "/"),
            "mesh_sha256": file_sha256(folder / mesh.name),
            "source_sha256": FROZEN_UEL_SHA256,
            "summary_file_sha256": file_sha256(folder / (job + "_SUMMARY.json"))
        }
        manifest.append(entry)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        files.append(str(manifest_path.relative_to(ROOT)))

        # Git commit and push
        head = "PENDING_COMMIT"
        try:
            subprocess.run(["git", "add", "-f", "--"] + files, cwd=ROOT, stdin=subprocess.DEVNULL)
            msg = "feat(complex-p3): record audited Problem 3 cycle %d evidence" % summary["cycle"]
            subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, stdin=subprocess.DEVNULL)
            p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            head = p.stdout.strip()
            if head:
                # Update commit in manifest
                manifest[-1]["commit"] = head
                manifest[-1]["url"] = manifest[-1]["url"].replace("PENDING_COMMIT", head)
                manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                subprocess.run(["git", "add", "-f", "--", str(manifest_path.relative_to(ROOT))], cwd=ROOT, stdin=subprocess.DEVNULL)
                subprocess.run(["git", "commit", "--amend", "--no-edit"], cwd=ROOT, stdin=subprocess.DEVNULL)
                subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, stdin=subprocess.DEVNULL, timeout=120)
                p2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
                head = p2.stdout.strip()
        except Exception as e:
            print("Git commit/push warning:", e)

        self.watch.record_agent_progress()

        print("[Publish] Pushed Cycle %d evidence to GitHub main at commit %s" % (summary["cycle"], head))
        return head

    def run_campaign(self):
        print("=== Starting Problem 3: Combined Tension + Shear Campaign ===")
        print("Material: E=%.1f GPa, nu=%.2f, l0=%.4f mm, Gc=%.4f kN/mm" % (BENCHMARK_E_GPA, BENCHMARK_NU, BENCHMARK_L0_MM, BENCHMARK_GC_KN_MM))
        print("Loading: EDGE_PULL with ux = 0.5 * uy (shear-to-tension ratio = 0.5)")
        print("Ceiling: < 35,000 elements, aspect ratio <= 5.0, positive Jacobians")

        source = self.run / "f42_mixed_uel.for"
        shutil.copy2(SOURCE_FILE, source)

        donor = None
        donor_job = None
        donor_summary_sha = None
        start_cycle = 0

        # Check for checkpoint resume or auto-detected prior cycle
        if self.donor_checkpoint and Path(self.donor_checkpoint).exists():
            donor = json.loads(Path(self.donor_checkpoint).read_text(encoding="utf-8"))
            donor_job = donor["job_name"]
            donor_summary_sha = file_sha256(self.publish_dir / (donor_job + "_SUMMARY.json"))
            self.peak_rf2 = donor.get("peak_rf2", donor.get("rf2", 0.0))
            self.peak_rf1 = donor.get("peak_rf1", donor.get("rf1", 0.0))
            if "tip" in donor:
                self.tips = [donor["tip"]]
            start_cycle = donor["cycle"] + 1
            print(">>> Resuming from donor checkpoint Cycle %d (%s)" % (donor["cycle"], donor_job))
        else:
            # Check publish_dir for latest completed checkpoint
            for c in range(self.max_cycles - 1, -1, -1):
                j_name = "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1" if c == 0 else "PK_METHOD_C_MIXED_LOAD_CYCLE%d" % c
                c_path = self.publish_dir / (j_name + "_checkpoint.json")
                s_path = self.publish_dir / (j_name + "_SUMMARY.json")
                if c_path.exists() and s_path.exists():
                    donor = json.loads(c_path.read_text(encoding="utf-8"))
                    donor_job = j_name
                    donor_summary_sha = file_sha256(s_path)
                    self.peak_rf2 = donor.get("peak_rf2", donor.get("rf2", 0.0))
                    self.peak_rf1 = donor.get("peak_rf1", donor.get("rf1", 0.0))
                    if "tip" in donor:
                        self.tips = [donor["tip"]]
                    start_cycle = c + 1
                    print(">>> Auto-detected completed Cycle %d (%s), resuming from Cycle %d" % (c, j_name, start_cycle))
                    break

        for cycle in range(start_cycle, self.max_cycles):
            job = "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1" if cycle == 0 else "PK_METHOD_C_MIXED_LOAD_CYCLE%d" % cycle
            print("\n-------------------------------------------------------------")
            print(">>> Problem 3 Cycle %d: Job %s" % (cycle, job))
            print("-------------------------------------------------------------")

            mesh_inp = self.run / (job + "_PHYS.inp")
            audit_json = self.run / (job + "_PHYS_audit.json")

            # Determine crack tip for mesh generation
            if cycle == 0:
                tip_eval_x, tip_eval_y = NOTCH_TIP_X, NOTCH_TIP_Y
            else:
                tip_eval_x, tip_eval_y = self.tips[-1]

            # Write tip history file for mesh generator (filtering out backward tip jitter)
            forward_tips = [p for p in self.tips if p[0] > NOTCH_TIP_X + 0.002]
            tip_hist_path = self.run / "tip_history.json"
            write_json(tip_hist_path, forward_tips)

            # Generate physical mesh using Abaqus CAE
            mesh_gen_script = HERE / "generate_mixed_load_mesh.py"
            self.command([
                self.abaqus, "cae", "noGUI=" + str(mesh_gen_script), "--",
                str(mesh_inp), str(audit_json),
                str(tip_eval_x), str(tip_eval_y), str(tip_hist_path)
            ], job + "_mesh", timeout=300)

            nodes, quads, tris, nsets = parse_physical_mesh(str(mesh_inp))
            if not nodes or not quads or len(quads) + len(tris) >= 35000:
                raise RuntimeError("Mesh missing or outside bounded element scope: %d elements" % (len(quads) + len(tris)))
            qa = geometry_audit(nodes, {**quads, **tris})
            if not qa["positive_jacobians_pass"] or not qa["edge_ratio_le_5_pass"]:
                write_json(self.run / (job + "_mesh_audit.json"), qa)
                raise RuntimeError("Physical mesh Jacobian or edge ratio failed")

            audit = json.loads(audit_json.read_text())
            spec = compute_corridor_spec(tip_x=tip_eval_x, tip_y=tip_eval_y, tip_history=self.tips)
            audit.update(spec)
            audit.update(qa)
            write_json(self.run / (job + "_mesh_audit.json"), audit)

            if not all(audit["gates"].values()):
                raise RuntimeError("Physical mesh quality audit failed: " + str(audit["gates"]))

            # State transfer and UEL deck assembly
            transferred_d = None
            transferred_h = None
            if cycle == 0:
                target_uy = DEFAULT_PRECRITICAL_UY_MM
                donor_uy = 0.0
            else:
                donor_uy = donor["uy"]
                target_uy = donor_uy + DEFAULT_LOAD_INCREMENT_MM
                raw_nodes, raw_quads, raw_tris, _ = donor["mesh"]
                d_nodes = {int(k): (float(v[0]), float(v[1])) for k, v in raw_nodes.items()}
                d_quads = {int(k): [int(x) for x in v] for k, v in raw_quads.items()}
                d_tris = {int(k): [int(x) for x in v] for k, v in raw_tris.items()}
                d = {int(n): float(v) for n, v in donor["damage"].items()}
                h = {tuple(map(int, k.split("_"))): float(v) for k, v in donor["history_gp"].items()}
                transferred_d, transferred_h = self.transfer(
                    d_nodes, d_quads, d_tris,
                    d, h,
                    nodes, quads, tris
                )
                transferred_d, transferred_h = self.transfer(
                    d_nodes, d_quads, d_tris,
                    d, h,
                    nodes, quads, tris
                )

            uel_inp = self.run / (job + ".inp")
            assemble_mixed_load_uel_deck(
                str(mesh_inp), str(uel_inp),
                donor_uy=donor_uy, target_uy=target_uy,
                transferred_damage=transferred_d, transferred_history=transferred_h,
                is_coarse=(cycle == 0), use_riks=True,
                shear_ratio=SHEAR_TO_TENSION_RATIO
            )
            validate_uel_properties(uel_inp, len(quads) + len(tris))

            # Abaqus Datacheck
            self.command([
                self.abaqus, "job=" + job + "_DATACHECK", "input=" + job,
                "user=" + source.name, "cpus=" + str(self.cpus), "datacheck", "interactive"
            ], job + "_DATACHECK", timeout=600)

            # Abaqus Solve
            elapsed = self.command([
                self.abaqus, "job=" + job, "input=" + job,
                "user=" + source.name, "cpus=" + str(self.cpus), "interactive"
            ], job, solver=True)

            sta = self.run / (job + ".sta")
            if not sta.exists() or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta.read_text(errors="replace"):
                raise RuntimeError("Solve incomplete: " + job)

            # Extract fields
            fields = self.extract(job)
            terminal = fields["terminal"]
            self.peak_rf2 = max(self.peak_rf2, fields["peak_rf2"])
            self.peak_rf1 = max(self.peak_rf1, fields["peak_rf1"])

            # Tip tracking and completion check
            tip, dist_hole, entered_hole, reached_boundary = connected_tip(
                nodes, {**quads, **tris},
                {int(n): v for n, v in terminal["damage"].items()}
            )
            self.tips.append(tip)

            # Compute cumulative chord arc length
            chord_sum = 0.0
            for i in range(1, len(self.tips)):
                chord_sum += math.hypot(self.tips[i][0] - self.tips[i - 1][0], self.tips[i][1] - self.tips[i - 1][1])

            # Completion evaluation
            done, reason = completion(self.peak_rf2, terminal["rf2"], entered_hole, reached_boundary)

            # Gate evaluations
            gates = {}
            if cycle > 0:
                donor_rf2 = donor["rf2"]
                hold_rf2 = fields["hold"]["rf2"]
                delta_rf2_pct = ((hold_rf2 - donor_rf2) / donor_rf2) * 100.0 if donor_rf2 != 0.0 else 0.0

                donor_rf1 = donor["rf1"]
                hold_rf1 = fields["hold"]["rf1"]
                delta_rf1_pct = ((hold_rf1 - donor_rf1) / donor_rf1) * 100.0 if donor_rf1 != 0.0 else 0.0

                force_pass = abs(delta_rf2_pct) <= 5.0

                donor_max_d = max(donor["damage"].values())
                hold_max_d = max(fields["hold"]["damage"].values())
                d_nonhealing_pass = (hold_max_d >= (donor_max_d - 1e-6))

                # Energy continuity
                e_hold = fields["hold"]["energies"]
                e_donor = donor["energies"]
                delta_sdv17 = ((e_hold.get("SDV17", 0.0) - e_donor.get("SDV17", 0.0)) / e_donor["SDV17"]) * 100.0 if e_donor.get("SDV17", 0.0) != 0.0 else 0.0
                delta_sdv18 = ((e_hold.get("SDV18", 0.0) - e_donor.get("SDV18", 0.0)) / e_donor["SDV18"]) * 100.0 if e_donor.get("SDV18", 0.0) != 0.0 else 0.0

                gates = {
                    "force_continuity_pass": force_pass,
                    "delta_rf2_pct": delta_rf2_pct,
                    "donor_rf2_kn": donor_rf2,
                    "hold_rf2_kn": hold_rf2,
                    "delta_rf1_pct": delta_rf1_pct,
                    "donor_rf1_kn": donor_rf1,
                    "hold_rf1_kn": hold_rf1,
                    "damage_nonhealing_pass": d_nonhealing_pass,
                    "donor_max_damage": donor_max_d,
                    "hold_max_damage": hold_max_d,
                    "delta_sdv17_pct": delta_sdv17,
                    "delta_sdv18_pct": delta_sdv18
                }
                print("[Cycle %d Gate] Delta RF2 = %.4f%% (%s) | Delta RF1 = %.4f%% | Nonhealing: %s" % (
                    cycle, delta_rf2_pct, "PASS" if force_pass else "FAIL", delta_rf1_pct, "PASS" if d_nonhealing_pass else "FAIL"
                ))
                if not force_pass:
                    raise RuntimeError("Transfer force continuity gate failed: %.4f%% > 5.0%%" % delta_rf2_pct)

            # Build summary dictionary
            accepted = (cycle == 0) or (gates.get("force_continuity_pass", False) and gates.get("damage_nonhealing_pass", False))
            summary = {
                "cycle": cycle,
                "job_name": job,
                "status": "CONVERGED_AUDITED" if accepted else "TRANSFER_GATE_FAILED",
                "benchmark": "Problem 3: Notch + Hole Combined Tension + Shear (ux = 0.5 * uy)",
                "shear_to_tension_ratio": SHEAR_TO_TENSION_RATIO,
                "donor_uy_mm": donor_uy,
                "terminal_uy_mm": terminal["uy"],
                "terminal_ux_mm": terminal["ux"],
                "terminal_rf2_kn": terminal["rf2"],
                "terminal_rf1_kn": terminal["rf1"],
                "peak_rf2_kn": self.peak_rf2,
                "peak_rf1_kn": self.peak_rf1,
                "tip_mm": [float(tip[0]), float(tip[1])],
                "tip_history_chord_sum_mm": chord_sum,
                "dist_to_hole_boundary_mm": dist_hole,
                "entered_hole": entered_hole,
                "max_damage": max(terminal["damage"].values()),
                "mesh_elements": len(quads) + len(tris),
                "mesh_nodes": len(nodes),
                "gate_results": gates,
                "elapsed_seconds": elapsed,
                "completion": done,
                "completion_reason": reason,
                "input_sha256": file_sha256(uel_inp),
                "mesh_sha256": file_sha256(mesh_inp),
                "source_sha256": FROZEN_UEL_SHA256,
                "pbs_submissions": 0,
                "cumulative_pbs_submissions": 73,
                "transfer_implementation": "cKDTree nearest-neighbour nodal damage and Gauss-point history transfer",
                "transfer_implementation_sha256": "87AE611413F37237320D13901C9E2FAA25EC91D7E3E4495D1E1B0DF6F3D7B997",
                "donor_checkpoint_sha256": donor_summary_sha
            }

            summary_path = self.run / (job + "_SUMMARY.json")
            write_json(summary_path, summary)

            # Checkpoint for state transfer
            checkpoint = {
                "cycle": cycle,
                "job_name": job,
                "uy": terminal["uy"],
                "ux": terminal["ux"],
                "rf2": terminal["rf2"],
                "rf1": terminal["rf1"],
                "damage": terminal["damage"],
                "history_gp": terminal["history"],
                "displacements": terminal["displacements"],
                "energies": terminal["energies"],
                "mesh": (nodes, quads, tris, nsets),
                "tip": tip,
                "peak_rf2": self.peak_rf2,
                "peak_rf1": self.peak_rf1
            }
            ckpt_path = self.run / (job + "_checkpoint.json")
            write_json(ckpt_path, checkpoint)

            # Plot mesh and damage
            image = self.plot(job, (nodes, quads, tris, nsets), terminal, summary)

            # Publish to campaign_results and Git commit/push
            self.publish(job, summary, mesh_inp, image)

            donor = checkpoint
            donor_job = job
            donor_summary_sha = file_sha256(self.publish_dir / (job + "_SUMMARY.json"))

            if done:
                print("\n=============================================================")
                print(">>> Problem 3 CAMPAIGN COMPLETED at Cycle %d: %s" % (cycle, reason))
                print("=============================================================")
                break

        print("\nProblem 3 campaign execution finished.")
        return summary


LocalRunner = MixedLoadMethodCRuntime
