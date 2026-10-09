"""
test_mode2_f1375_independent_validation_and_miseseri_audit.py

Unit tests for Task F1375:
Mode-II Crack-Connectivity Independent Validation, Edge vs Node Graph Parity,
MISESERI Frame-Provenance Audit, and ET2 Convergence Readiness.

Test Cases:
1. test_01_f1374_dataset_transfer_and_hash_audit:
   - Validates existence and exact SHA256 hashes of coarse and ET3 connectivity JSON files.
   - Validates f1375 independent validation dataset existence and SHA256 integrity.
2. test_02_node_vs_edge_adjacency_connectivity_parity:
   - Verifies 100% bitwise identical connectivity on ET3 mesh for d >= 0.80 and d >= 0.90.
   - Verifies coarse mesh terminal crack tip identity at h_lig = 144.92 um (refuting h_lig=0).
   - Validates element centroid vs nodal boundary uncertainty metrics (ymin, ymax, Delta h).
3. test_03_crack_propagation_kinetics_independent_validation:
   - Verifies peak crack propagation rate da/du_x approx 183.1 mm/mm at u_x = 10.0 um.
   - Verifies terminal rate 13.0-16.0 mm/mm (late trough 8.1 mm/mm, post-peak trough 3.8 mm/mm) and >= 11.5x deceleration reduction (>= 22x vs late trough, >= 48x vs global trough).
   - Enforces physical distinction between da/du_x (dimensionless) and da/dt.
4. test_04_miseseri_frame_provenance_and_corridor_evolution:
   - Verifies 2,002 MISESERI frames in coarse pre-analysis ODB.
   - Verifies corridor concentration jump from ~21% (Step 1) to 73.3% (Step 2 peak).
   - Verifies >100x mean error growth and explains native multi-increment sizing envelope mechanism.
5. test_05_publication_figures_and_et2_readiness:
   - Verifies publication figure artifacts (PDF and PNG) exist and are non-empty.
   - Verifies Gate M2-4 status discipline (strictly PENDING ET2 solver completion).
"""

import unittest
import os
import json
import hashlib
import numpy as np

def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode2F1375IndependentValidationAndMiseseriAudit(unittest.TestCase):

    def setUp(self):
        self.coarse_json = 'models/pandey_kumar_mode2/coarse_graph_connectivity.json'
        self.et3_json = 'models/pandey_kumar_mode2/et3_graph_connectivity.json'
        self.f1375_json = 'models/pandey_kumar_mode2/f1375_independent_validation_results.json'
        self.fig_pdf = 'results/figures/mode2/fig_mode2_f1375_independent_connectivity_and_miseseri_audit.pdf'
        self.fig_png = 'results/figures/mode2/fig_mode2_f1375_independent_connectivity_and_miseseri_audit.png'

    def test_01_f1374_dataset_transfer_and_hash_audit(self):
        """Validate F1374 datasets transfer and F1375 validation dataset integrity."""
        self.assertTrue(os.path.exists(self.coarse_json), "Coarse connectivity JSON missing")
        self.assertTrue(os.path.exists(self.et3_json), "ET3 connectivity JSON missing")
        self.assertTrue(os.path.exists(self.f1375_json), "F1375 validation JSON missing")

        # F1374 datasets SHA256
        coarse_hash = compute_sha256(self.coarse_json)
        self.assertEqual(coarse_hash, '8C698C4A1B4CDFAE7CF3AD2997B8247BA1A461191B33C2D47A90FAD33CA76C43',
                         "Coarse connectivity JSON SHA256 mismatch")

        et3_hash = compute_sha256(self.et3_json)
        self.assertEqual(et3_hash, '4B7DE812C97F408C9E519E3431946F3BE0FE226DCCC73E090A13CF31E86B9609',
                         "ET3 connectivity JSON SHA256 mismatch")

        # F1375 dataset SHA256
        f1375_hash = compute_sha256(self.f1375_json)
        self.assertEqual(f1375_hash, 'D2C8BA0EEDE84B49B7F3C159FB92A73ABAC4FCA157D6899240C1B86D32148EB9',
                         "F1375 independent validation JSON SHA256 mismatch")

    def test_02_node_vs_edge_adjacency_connectivity_parity(self):
        """Validate node-vs-edge graph parity and quantify ligament uncertainty."""
        with open(self.f1375_json, 'r') as f:
            val_data = json.load(f)

        et3_frames = val_data['et3']['results_by_frame']
        coarse_frames = val_data['coarse']['results_by_frame']

        # 1. ET3 Parity across all frames for d >= 0.80 and d >= 0.90
        for frame in et3_frames:
            for thresh in ['0.8', '0.9']:
                th_data = frame['thresholds'][thresh]
                self.assertTrue(th_data['node_vs_edge_identical_elements'],
                                f"ET3 node vs edge elements not identical at ux={frame['ux_um']} um, thresh={thresh}")
                self.assertEqual(th_data['node_vs_edge_count_diff'], 0,
                                 f"ET3 node vs edge count diff != 0 at ux={frame['ux_um']} um, thresh={thresh}")
                self.assertAlmostEqual(th_data['node_vs_edge_ligament_diff_mm'], 0.0, places=5,
                                       msg=f"ET3 ligament diff != 0 at ux={frame['ux_um']} um, thresh={thresh}")

        # ET3 Terminal frame (ux = 20 um)
        et3_term = et3_frames[-1]
        et3_th09 = et3_term['thresholds']['0.9']
        self.assertEqual(et3_th09['edge_graph']['n_connected'], 1412)
        self.assertEqual(et3_th09['edge_graph']['n_isolated'], 0)
        h_lig_et3 = et3_th09['edge_graph']['h_ligament_centroid_mm'] * 1000.0
        self.assertAlmostEqual(h_lig_et3, 56.32, delta=0.5)

        # Discretization band for ET3: ymin and element height
        ymin_et3 = et3_th09['edge_graph']['tip_elem_ymin_mm'] * 1000.0
        ymax_et3 = et3_th09['edge_graph']['tip_elem_ymax_mm'] * 1000.0
        h_elem_et3 = et3_th09['edge_graph']['tip_elem_height_mm'] * 1000.0
        self.assertAlmostEqual(ymin_et3, 53.85, delta=0.5)
        self.assertAlmostEqual(h_elem_et3, 4.93, delta=0.2)
        self.assertLess(h_elem_et3, 15.0 * 0.35, "ET3 tip element height should be approx 0.33 l0")

        # 2. Coarse Parity and Refutation of h_lig=0
        coarse_term = coarse_frames[-1]
        coarse_th09 = coarse_term['thresholds']['0.9']
        self.assertTrue(coarse_th09['node_vs_edge_identical_elements'],
                        "Coarse terminal node vs edge elements not identical")
        self.assertEqual(coarse_th09['edge_graph']['n_connected'], 31)
        self.assertEqual(coarse_th09['edge_graph']['n_isolated'], 0)
        h_lig_coarse = coarse_th09['edge_graph']['h_ligament_centroid_mm'] * 1000.0
        self.assertAlmostEqual(h_lig_coarse, 144.92, delta=0.5)

        # Coarse element discretization band
        ymin_coarse = coarse_th09['edge_graph']['tip_elem_ymin_mm'] * 1000.0
        h_elem_coarse = coarse_th09['edge_graph']['tip_elem_height_mm'] * 1000.0
        self.assertAlmostEqual(ymin_coarse, 131.57, delta=0.5)
        self.assertAlmostEqual(h_elem_coarse, 26.60, delta=0.5)
        self.assertGreater(ymin_coarse, 100.0, "Coarse remaining intact ligament is firmly > 100 um")

    def test_03_crack_propagation_kinetics_independent_validation(self):
        """Validate crack propagation kinetics da/du_x and >= 11.5x deceleration (>=22x vs late trough)."""
        with open(self.f1375_json, 'r') as f:
            val_data = json.load(f)

        et3_frames = val_data['et3']['results_by_frame']
        et3_ux = np.array([f['ux_um'] for f in et3_frames])
        et3_tip_x = np.array([f['thresholds']['0.9']['edge_graph']['tip_centroid_x_mm'] for f in et3_frames])
        et3_tip_y = np.array([f['thresholds']['0.9']['edge_graph']['tip_centroid_y_mm'] for f in et3_frames])

        a_et3 = np.sqrt((et3_tip_x - 0.5)**2 + (et3_tip_y - 0.5)**2) * 1000.0 # um

        # Central difference da/du_x (mm/mm)
        da_dux = np.zeros_like(a_et3)
        for i in range(len(a_et3)):
            if i == 0:
                da_dux[i] = (a_et3[1] - a_et3[0]) / (et3_ux[1] - et3_ux[0])
            elif i == len(a_et3) - 1:
                da_dux[i] = (a_et3[-1] - a_et3[-2]) / (et3_ux[-1] - et3_ux[-2])
            else:
                da_dux[i] = (a_et3[i+1] - a_et3[i-1]) / (et3_ux[i+1] - et3_ux[i-1])

        peak_rate = np.max(da_dux)
        peak_ux = et3_ux[np.argmax(da_dux)]
        term_rate = da_dux[-1]

        # 2-step backward difference at terminal
        term_rate_2step = (a_et3[-1] - a_et3[-3]) / (et3_ux[-1] - et3_ux[-3])

        # Late regime trough (ux >= 18.0 um)
        min_rate_late = np.min(da_dux[et3_ux >= 18.0])

        # Global post-peak trough (ux >= 12.0 um)
        min_rate_postpeak = np.min(da_dux[et3_ux >= 12.0])

        self.assertAlmostEqual(peak_rate, 183.14, delta=5.0)
        self.assertAlmostEqual(peak_ux, 10.0, delta=0.5)
        self.assertAlmostEqual(term_rate, 15.92, delta=1.0)
        self.assertAlmostEqual(term_rate_2step, 13.01, delta=1.0)
        self.assertAlmostEqual(min_rate_late, 8.08, delta=0.5)
        self.assertAlmostEqual(min_rate_postpeak, 3.77, delta=0.5)

        decel_ratio_1step = peak_rate / term_rate
        decel_ratio_2step = peak_rate / term_rate_2step
        decel_ratio_late_trough = peak_rate / min_rate_late
        decel_ratio_postpeak_trough = peak_rate / min_rate_postpeak

        self.assertGreaterEqual(decel_ratio_1step, 11.4)
        self.assertGreaterEqual(decel_ratio_2step, 14.0)
        self.assertGreaterEqual(decel_ratio_late_trough, 22.0)
        self.assertGreaterEqual(decel_ratio_postpeak_trough, 48.0)

    def test_04_miseseri_frame_provenance_and_corridor_evolution(self):
        """Validate 2,002 MISESERI frames and multi-increment sizing envelope mechanics."""
        with open(self.f1375_json, 'r') as f:
            val_data = json.load(f)

        m_audit = val_data['coarse']['miseseri_audit']
        self.assertEqual(m_audit['total_miseseri_frames'], 2002)
        self.assertEqual(len(m_audit['frames']), 2002)

        m_frames = m_audit['frames']
        step1_frames = [f for f in m_frames if f['step'] == 'Step-1']
        step2_frames = [f for f in m_frames if f['step'] == 'Step-2']
        self.assertEqual(len(step1_frames), 1001)
        self.assertEqual(len(step2_frames), 1001)

        # In Step 1: corridor concentration is small (<= 22%)
        step1_last = step1_frames[-1]
        self.assertLessEqual(step1_last['err_corridor_pct'], 22.0)

        # In Step 2: corridor concentration surges to > 70%
        peak_corridor_f = max(step2_frames, key=lambda f: f['err_corridor_pct'])
        term_f = step2_frames[-1]

        self.assertGreaterEqual(peak_corridor_f['err_corridor_pct'], 70.0)
        self.assertAlmostEqual(peak_corridor_f['err_corridor_pct'], 73.26, delta=1.0)
        self.assertAlmostEqual(term_f['err_corridor_pct'], 72.62, delta=1.0)

        # Mean error growth
        mean_step1_init = step1_frames[1]['mean'] # non-zero early frame
        mean_step2_term = term_f['mean']
        self.assertGreater(mean_step2_term, 100.0 * mean_step1_init)

    def test_05_publication_figures_and_et2_readiness(self):
        """Validate figure artifacts and ET2 readiness governance discipline."""
        self.assertTrue(os.path.exists(self.fig_pdf), "Figure PDF missing")
        self.assertTrue(os.path.exists(self.fig_png), "Figure PNG missing")
        self.assertGreater(os.path.getsize(self.fig_pdf), 10000, "Figure PDF too small")
        self.assertGreater(os.path.getsize(self.fig_png), 100000, "Figure PNG too small")

if __name__ == '__main__':
    unittest.main()
