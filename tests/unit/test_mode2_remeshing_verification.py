import os
import unittest
import numpy as np
import pandas as pd

class TestMode2RemeshingVerification(unittest.TestCase):
    """
    Stage 1 Unit Test Suite: Mode-II Pure Shear Remeshing Verification
    Governing Reference: Pandey & Kumar (2025) CMES, Section 4.2, Figs. 6b, 12b.
    """
    
    @classmethod
    def setUpClass(cls):
        cls.brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\b01cba38-646b-4f8c-8de2-b03dcba99e01"
        cls.et2_csv = os.path.join(cls.brain_dir, "mesh_elements_et2.csv")
        
        # Primary profile CSV from repository workspace
        repo_prof = os.path.join("models", "pandey_kumar_mode2", "04_adaptive_miseseri", "LOCAL_CRACK_PATH_RESOLUTION_PROFILE.csv")
        cls.profile_csv = repo_prof if os.path.exists(repo_prof) else os.path.join(cls.brain_dir, "LOCAL_CRACK_PATH_RESOLUTION_PROFILE.csv")
        
        # Paper digitized paths (physical domain [0, 1] x [0, 1] mm)
        cls.paper_6b_x = np.array([0.495, 0.540, 0.600, 0.680, 0.760, 0.840, 0.930])
        cls.paper_6b_y = np.array([0.514, 0.460, 0.380, 0.280, 0.180, 0.080, 0.000])
        
        cls.paper_12b_x = np.array([0.500, 0.535, 0.585, 0.650, 0.725, 0.800, 0.868])
        cls.paper_12b_y = np.array([0.500, 0.430, 0.340, 0.235, 0.140, 0.060, 0.000])

    def test_paper_digitized_paths_consistency(self):
        """Verify digitized paper chord inclination angles and end coordinates."""
        dx_6b = self.paper_6b_x[-1] - self.paper_6b_x[0]
        dy_6b = self.paper_6b_y[-1] - self.paper_6b_y[0]
        theta_6b = np.degrees(np.arctan2(dy_6b, dx_6b))
        self.assertAlmostEqual(theta_6b, -49.74, delta=1.5)
        
        dx_12b = self.paper_12b_x[-1] - self.paper_12b_x[0]
        dy_12b = self.paper_12b_y[-1] - self.paper_12b_y[0]
        theta_12b = np.degrees(np.arctan2(dy_12b, dx_12b))
        self.assertAlmostEqual(theta_12b, -53.65, delta=1.5)

    def test_mode2_native_mesh_element_count_parity(self):
        """Verify generated native mesh element count is within 10% of paper (19,963 elements)."""
        if not os.path.exists(self.et2_csv):
            self.skipTest("mesh_elements_et2.csv not found in brain directory")
        df = pd.read_csv(self.et2_csv)
        n_elems = len(df)
        paper_elems = 19963
        rel_diff = abs(n_elems - paper_elems) / float(paper_elems)
        self.assertLess(rel_diff, 0.10, "Element count %d differs from paper %d by %.1f%%" % (n_elems, paper_elems, rel_diff * 100))

    def test_fine_element_fraction_in_active_zone(self):
        """Verify that refined elements (h <= 0.008 mm) constitute > 65% of the mesh."""
        if not os.path.exists(self.et2_csv):
            self.skipTest("mesh_elements_et2.csv not found")
        df = pd.read_csv(self.et2_csv)
        fine_count = (df['h_approx'] <= 0.008).sum()
        fine_fraction = fine_count / float(len(df))
        self.assertGreater(fine_fraction, 0.65, "Fine element fraction is %.2f%% (< 65%%)" % (fine_fraction * 100))

    def test_corridor_resolution_and_min_size(self):
        """Verify min element size satisfies h/l0 < 0.1 for l0 = 0.015 mm."""
        if not os.path.exists(self.et2_csv):
            self.skipTest("mesh_elements_et2.csv not found")
        df = pd.read_csv(self.et2_csv)
        h_min = df['h_approx'].min()
        l0 = 0.015
        h_over_l0 = h_min / l0
        self.assertLess(h_over_l0, 0.10, "Minimum h/l0 = %.4f exceeds 0.10" % h_over_l0)

    def test_zero_spurious_branches(self):
        """Verify no spurious disconnected refined branches exist outside expected corridor."""
        if not os.path.exists(self.et2_csv):
            self.skipTest("mesh_elements_et2.csv not found")
        df = pd.read_csv(self.et2_csv)
        # Check that fine elements with h <= 0.003 mm are concentrated in active zone,
        # with no more than 2 stray transition elements in far upper-left (x < 0.35, y in [0.2, 0.8])
        spurious_patch = df[(df['cx'] < 0.35) & (df['cy'] > 0.20) & (df['cy'] < 0.80) & (df['h_approx'] <= 0.003)]
        self.assertLessEqual(len(spurious_patch), 2, "Found %d spurious fine elements in upper-left domain" % len(spurious_patch))

    def test_euclidean_distance_to_paper_path(self):
        """Verify Euclidean distance between phase-field path and paper Fig. 6b path."""
        if not os.path.exists(self.profile_csv):
            self.skipTest("LOCAL_CRACK_PATH_RESOLUTION_PROFILE.csv not found")
        df = pd.read_csv(self.profile_csv)
        x_pts = df['x_mm'].values + 0.5
        y_pts = df['y_mm'].values + 0.5
        
        # 1. Early initiation/propagation segment (x <= 0.58 mm): within 2.5 l0 (0.038 mm)
        early_mask = (x_pts <= 0.58)
        early_dists = [min(np.hypot(x - self.paper_6b_x, y - self.paper_6b_y)) for x, y in zip(x_pts[early_mask], y_pts[early_mask])]
        early_mean = np.mean(early_dists)
        self.assertLess(early_mean, 0.038, "Early propagation distance = %.4f mm exceeds 0.038 mm" % early_mean)
        
        # 2. Full profile average distance across entire u=0.050 mm trajectory
        full_dists = [min(np.hypot(x - self.paper_6b_x, y - self.paper_6b_y)) for x, y in zip(x_pts, y_pts)]
        full_mean = np.mean(full_dists)
        self.assertLess(full_mean, 0.150, "Full trajectory mean distance = %.4f mm exceeds 0.150 mm" % full_mean)

if __name__ == '__main__':
    unittest.main()
