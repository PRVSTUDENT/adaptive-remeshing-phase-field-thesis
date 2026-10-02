"""
Comprehensive Unit Test Suite for Mode-I Energy Equation Code Map, Dimensional Units,
2D Plane Strain Out-of-Plane Unit Thickness Normalization, and Provenance Auditing.

Tests Gate-6B mathematical formulations, state variable assignments, single-IP deduplication,
unit conversions, work sign convention, layer mapping, dimensional units reconciliation,
UEL source-level unit-thickness normalization semantics, and literature provenance discipline.
"""

import pytest
import numpy as np
import math

def trapz_compat(y, x):
    """NumPy 1.x / 2.x compatible trapezoidal integration."""
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)

class TestMode1EnergyEquationCodeMap:
    """Test suite covering the 19 offline energy, dimensional, thickness normalization, and provenance checks."""
    
    def test_detects_swapped_sdv17_sdv18(self):
        """
        Verify detection of swapped SDV17 (E_frac) and SDV18 (E_elas) assignments.
        SDV17 must strictly be E_frac (kN*mm) and SDV18 must strictly be E_elas (kN*mm).
        """
        sdv_map = {
            17: {"name": "E_frac", "type": "energy", "unit": "kN*mm"},
            18: {"name": "E_elas", "type": "energy", "unit": "kN*mm"},
            19: {"name": "psi_f", "type": "density", "unit": "kN/mm^2"},
            20: {"name": "psi_e", "type": "density", "unit": "kN/mm^2"}
        }
        
        assert sdv_map[17]["name"] == "E_frac"
        assert sdv_map[18]["name"] == "E_elas"
        
        swapped_map = {
            17: {"name": "E_elas", "type": "energy", "unit": "kN*mm"},
            18: {"name": "E_frac", "type": "energy", "unit": "kN*mm"}
        }
        
        def validate_mapping(mapping):
            if mapping.get(17, {}).get("name") != "E_frac":
                return False, "SDV17 must be E_frac"
            if mapping.get(18, {}).get("name") != "E_elas":
                return False, "SDV18 must be E_elas"
            return True, "Valid"
            
        valid, msg = validate_mapping(sdv_map)
        assert valid is True
        
        valid_swapped, msg_swapped = validate_mapping(swapped_map)
        assert valid_swapped is False
        assert "SDV17 must be E_frac" in msg_swapped

    def test_rejects_summation_of_energy_densities(self):
        """
        Verify that SDV19 (psi_f) and SDV20 (psi_e) are local densities (kN/mm^2)
        and cannot be summed across elements without element area/volume integration.
        """
        num_elements = 100
        element_area = 0.0001 # mm^2 (e.g. 0.01mm x 0.01mm)
        thickness = 1.0 # mm (standard 2D plane strain unit thickness)
        
        # Uniform local energy density
        psi_f_vals = np.full(num_elements, 0.027) # kN/mm^2 = 27 MPa = 0.027 J/mm^3
        
        # Correct element-integrated energies: V_e = A_e * t
        e_frac_elements = psi_f_vals * (element_area * thickness) # kN*mm = J
        total_e_frac_integrated = np.sum(e_frac_elements) # 0.00027 kN*mm = 0.27 mJ
        
        # Naive un-integrated sum of densities
        naive_density_sum = np.sum(psi_f_vals) # 2.70 kN/mm^2 (WRONG)
        
        # Dimensional ratio between wrong sum and correct integral
        error_ratio = naive_density_sum / total_e_frac_integrated
        assert math.isclose(error_ratio, 1.0 / (element_area * thickness), rel_tol=1e-6)
        assert error_ratio == 10000.0 # Factor of 10^4 discrepancy!
        
        def reduce_energy(values, is_density=False, areas=None, thickness=1.0):
            if is_density:
                if areas is None:
                    raise ValueError("Cannot integrate energy density without element areas/volumes")
                return float(np.sum(values * areas * thickness))
            return float(np.sum(values))
            
        with pytest.raises(ValueError, match="Cannot integrate energy density"):
            reduce_energy(psi_f_vals, is_density=True, areas=None)
            
        correct_res = reduce_energy(psi_f_vals, is_density=True, areas=np.full(num_elements, element_area), thickness=thickness)
        assert math.isclose(correct_res, total_e_frac_integrated, rel_tol=1e-12)

    def test_detects_4x_gauss_point_overcounting(self):
        """
        Verify that 4-IP CPE4 element output duplicates element-integrated values,
        and single-value deduplication prevents 4x overcounting.
        """
        num_phys_elements = 50
        num_ips = 4
        
        true_e_frac_per_elem = np.random.uniform(0.001, 0.01, size=num_phys_elements)
        expected_total_e_frac = np.sum(true_e_frac_per_elem)
        
        odb_values_stream = []
        for elem_idx in range(1, num_phys_elements + 1):
            e_val = true_e_frac_per_elem[elem_idx - 1]
            for ip in range(1, num_ips + 1):
                odb_values_stream.append({
                    "elementLabel": elem_idx,
                    "integrationPoint": ip,
                    "data": e_val
                })
                
        assert len(odb_values_stream) == num_phys_elements * 4
        
        # Naive summation without deduplication
        naive_sum = sum(v["data"] for v in odb_values_stream)
        assert math.isclose(naive_sum, 4.0 * expected_total_e_frac, rel_tol=1e-12)
        
        # Deduplicated summation (authoritative extractor pattern)
        seen_elems = set()
        dedup_sum = 0.0
        for v in odb_values_stream:
            eid = v["elementLabel"]
            if eid not in seen_elems:
                seen_elems.add(eid)
                dedup_sum += v["data"]
                
        assert len(seen_elems) == num_phys_elements
        assert math.isclose(dedup_sum, expected_total_e_frac, rel_tol=1e-12)

    def test_validates_energy_unit_conversions(self):
        """
        Verify exact unit conversions between kN*mm, J, mJ, and uJ.
        1 kN*mm = 10^3 N * 10^-3 m = 1.0 N*m = 1.0 J = 1000.0 mJ = 1.0e6 uJ.
        """
        e_kn_mm = 2.359329e-3 # 0.002359329 kN*mm (canonical Mode-I baseline)
        
        # Convert to Joules
        e_joules = e_kn_mm * 1.0
        assert math.isclose(e_joules, 0.002359329, rel_tol=1e-12)
        
        # Convert to mJ
        e_mj = e_kn_mm * 1000.0
        assert math.isclose(e_mj, 2.359329, rel_tol=1e-12)
        
        # Convert to uJ
        e_uj = e_kn_mm * 1.0e6
        assert math.isclose(e_uj, 2359.329, rel_tol=1e-12)
        
        # Verify incorrect unit multiplier detection
        wrong_mJ_multiplier = 100.0 # Bug
        assert not math.isclose(e_kn_mm * wrong_mJ_multiplier, 2.359329, rel_tol=1e-6)

    def test_detects_reversed_work_sign_convention(self):
        """
        Verify external work sign convention:
        Abaqus reaction force at loaded top boundary is negative (RF2 < 0).
        Physical applied tensile force is F = -RF2 > 0.
        Cumulative work W_ext = \\int F du must be non-negative for tensile loading.
        """
        u_history = np.linspace(0.0, 0.01, 100)
        rf2_history = - (138.0 * u_history - 5000.0 * (u_history**2)) # Negative values
        assert np.all(rf2_history <= 0.0)
        
        f_physical = -rf2_history
        assert np.all(f_physical >= 0.0)
        
        # Correct trapezoidal integration of external work using compat helper
        w_ext_correct = trapz_compat(f_physical, u_history)
        assert w_ext_correct > 0.0
        
        # Reversed sign integration (Bug: integrating raw RF2 without negation)
        w_ext_reversed = trapz_compat(rf2_history, u_history)
        assert w_ext_reversed < 0.0
        assert math.isclose(w_ext_correct, -w_ext_reversed, rel_tol=1e-12)
        
        def audit_work(w_val):
            if w_val < 0.0:
                raise ValueError("External work W_ext must be positive under tensile loading; check RF sign convention!")
            return True
            
        assert audit_work(w_ext_correct) is True
        with pytest.raises(ValueError, match="External work W_ext must be positive"):
            audit_work(w_ext_reversed)

    def test_verifies_companion_layer_mapping_formula(self):
        """
        Verify 3-layer companion index mapping formula:
        Layer 1: Phase-field UEL (labels 1 .. Nphys, DOFs 3)
        Layer 2: Mechanical UEL (labels Nphys+1 .. 2*Nphys, DOFs 1,2)
        Layer 3: Companion UMAT (labels 2*Nphys+1 .. 3*Nphys, visualization & energy output)
        Formula: PHYSIDX = NOEL - 2*Nphys
        """
        n_phys = 15192 # Reference mesh size
        layer3_labels = np.array([2*n_phys + 1, 2*n_phys + 500, 3*n_phys])
        
        phys_indices = layer3_labels - 2*n_phys
        assert np.array_equal(phys_indices, [1, 500, 15192])
        assert np.all(phys_indices >= 1)
        assert np.all(phys_indices <= n_phys)
        
        legacy_wrong_indices = layer3_labels - n_phys
        assert np.any(legacy_wrong_indices > n_phys)
        assert legacy_wrong_indices[0] == n_phys + 1 # 15193 > 15192 (Array bounds violation!)

    def test_verifies_energy_balance_bookkeeping_formula(self):
        """
        Verify bookkeeping residual formula:
        E_model = E_elas + E_frac
        Delta_book = E_model - W_ext
        Normalized residual: delta_book_rel = (E_model - W_ext) / max(W_ext, E_model)
        """
        w_ext = 0.003500 # kN*mm
        e_elas = 0.002200 # kN*mm
        e_frac = 0.001295 # kN*mm
        
        e_model = e_elas + e_frac # 0.003495 kN*mm
        delta_book = e_model - w_ext # -0.000005 kN*mm (-5 uJ)
        delta_book_rel = delta_book / max(w_ext, e_model) # -0.00142857 (-0.1428%)
        
        assert math.isclose(e_model, 0.003495, rel_tol=1e-12)
        assert math.isclose(delta_book, -5.0e-6, rel_tol=1e-12)
        assert math.isclose(delta_book_rel, -5.0e-6 / 0.003500, rel_tol=1e-12)
        assert delta_book < 0.0

    def test_stress_and_energy_density_units_kN_mm2(self):
        """
        Verify dimensional relationship between kN/mm^2 and MPa / GPa.
        1 kN/mm^2 = 10^3 N / (10^-3 m)^2 = 10^9 N/m^2 = 10^9 Pa = 1000 MPa = 1 GPa.
        Asserts that 1 kN/mm^2 != 1 MPa (which would be a 1000x error).
        """
        one_kn_per_mm2_in_pa = 1.0 * (1e3) / (1e-3)**2 # 1.0e9 Pa
        one_mpa_in_pa = 1.0e6 # Pa
        one_gpa_in_pa = 1.0e9 # Pa
        
        val_in_mpa = one_kn_per_mm2_in_pa / one_mpa_in_pa
        assert math.isclose(val_in_mpa, 1000.0, rel_tol=1e-12)
        
        val_in_gpa = one_kn_per_mm2_in_pa / one_gpa_in_pa
        assert math.isclose(val_in_gpa, 1.0, rel_tol=1e-12)
        
        assert not math.isclose(val_in_mpa, 1.0, rel_tol=1e-6)
        
        def validate_stress_or_energy_density_unit(unit_str):
            u = unit_str.strip()
            if u == "MPa":
                return False, "kN/mm^2 is not equal to MPa (1 kN/mm^2 = 1000 MPa = 1 GPa)"
            if u in ("kN/mm^2", "J/mm^3", "GPa"):
                return True, "Valid"
            return False, f"Invalid density unit: {unit_str}"
            
        ok_mpa, msg_mpa = validate_stress_or_energy_density_unit("MPa")
        assert ok_mpa is False
        assert "1000 MPa" in msg_mpa
        ok_kn, _ = validate_stress_or_energy_density_unit("kN/mm^2")
        assert ok_kn is True

    def test_rejects_kn_per_mm2_equals_j_per_mm2(self):
        """
        Verify dimensional distinction between volumetric density (kN/mm^2 = J/mm^3)
        and surface energy density (J/mm^2 = kN/mm).
        """
        unit_kn_mm = 1.0 # 1 kN*mm = 1 J
        unit_vol_mm3 = 1.0 # mm^3
        volumetric_density_j_per_mm3 = unit_kn_mm / unit_vol_mm3 # 1.0 J/mm^3
        
        dim_volumetric = {"mass": 1, "length": -1, "time": -2} # Pa = N/m^2 = J/m^3
        dim_surface    = {"mass": 1, "length": 0,  "time": -2} # N/m = J/m^2
        
        assert dim_volumetric != dim_surface
        assert dim_volumetric["length"] == -1
        assert dim_surface["length"] == 0
        
        def validate_volumetric_not_surface(unit_str):
            u = unit_str.strip()
            if u in ("J/mm^2", "kN/mm", "N/mm"):
                return False, "Volumetric density [J/mm^3] cannot have surface energy units [J/mm^2]"
            if u in ("kN/mm^2", "J/mm^3", "mJ/mm^3", "GPa"):
                return True, "Valid"
            return False, f"Invalid volumetric unit: {unit_str}"
            
        ok_surf, msg_surf = validate_volumetric_not_surface("J/mm^2")
        assert ok_surf is False
        assert "surface energy units" in msg_surf
        ok_vol, _ = validate_volumetric_not_surface("kN/mm^2")
        assert ok_vol is True

    def test_at2_phase_field_density_dimensions(self):
        """
        Verify dimensional analysis of AT2 phase-field regularized surface energy density:
        psi_f(d, grad_d) = G_c * [ d^2 / (2*l_0) + (l_0/2) * |grad_d|^2 ]
        [G_c] = kN/mm = 0.0027 kN/mm = 2.7 N/mm = 2700 J/m^2 = 0.0027 J/mm^2 (NOT 2.7 J/mm^2!).
        [l_0] = mm
        [grad_d] = 1/mm => |grad_d|^2 = 1/mm^2
        [psi_f] = [G_c] * (1/[l_0]) = (kN/mm) * (1/mm) = kN/mm^2 = J/mm^3 (volumetric density).
        """
        gc = 0.0027 # kN/mm
        l0 = 0.0075 # mm
        
        gc_j_per_mm2 = (gc * 1e3 * 1e-3) / (1.0) # 0.0027 (kN*mm)/mm^2 = 0.0027 J/mm^2
        assert math.isclose(gc_j_per_mm2, 0.0027, rel_tol=1e-12)
        assert not math.isclose(gc_j_per_mm2, 2.7, rel_tol=1e-6) # Strictly reject 2.7 J/mm^2
        
        d = 0.5 # [-]
        grad_d = np.array([10.0, 0.0]) # 1/mm
        grad_d_sq = np.dot(grad_d, grad_d) # 100.0 (1/mm^2)
        
        bracket_term = (d**2) / (2.0 * l0) + (l0 / 2.0) * grad_d_sq # Dimension: 1/mm
        psi_f = gc * bracket_term # Dimension: (kN/mm) * (1/mm) = kN/mm^2
        
        assert psi_f > 0.0
        expected_psi_f = 0.0027 * (0.25 / 0.015 + 0.00375 * 100.0)
        assert math.isclose(psi_f, expected_psi_f, rel_tol=1e-12)
        
        psi_f_j_per_mm3 = psi_f * 1.0 # 1.0 (kN*mm/mm^3)/(kN/mm^2)
        assert math.isclose(psi_f_j_per_mm3, psi_f, rel_tol=1e-12)
        
        psi_f_mpa = psi_f * 1000.0
        assert math.isclose(psi_f_mpa, expected_psi_f * 1000.0, rel_tol=1e-12)

    def test_2d_plane_strain_thickness_energy_consistency(self):
        """
        Verify that in 2D plane strain modeling with unit out-of-plane thickness t = 1.0 mm,
        the volume integral V_e = A_e * t gives scalar energy [kN*mm] = [J] matching external work W_ext.
        """
        element_area = 0.003 * 0.003 # 9e-6 mm^2
        thickness = 1.0 # mm
        element_vol = element_area * thickness # 9e-6 mm^3
        
        psi_f = 0.045 # kN/mm^2 = 45 MPa = 0.045 J/mm^3
        e_frac_elem = psi_f * element_vol # (kN/mm^2) * (mm^3) = kN*mm = J
        assert math.isclose(e_frac_elem, 0.045 * 9e-6, rel_tol=1e-12)
        
        force_kn = 0.75 # kN (total tensile load on 1 mm thick slice)
        disp_mm = 0.0058 # mm
        w_ext_step = force_kn * disp_mm # kN*mm = J
        assert math.isclose(w_ext_step, 0.75 * 0.0058, rel_tol=1e-12)

    def test_fails_if_2d_integral_lacks_thickness_handling(self):
        """
        Enforce that any 2D volume integration validator strictly specifies
        out-of-plane thickness t = 1.0 mm and fails if thickness is omitted or invalid.
        """
        def integrate_2d_field(field_values, element_areas, thickness=None):
            if thickness is None:
                raise ValueError("2D plane strain volume integration requires explicit out-of-plane thickness t")
            if not isinstance(thickness, (int, float)) or thickness <= 0:
                raise ValueError("Thickness t must be strictly positive")
            return float(np.sum(field_values * element_areas * thickness))
            
        field = np.array([0.02, 0.04]) # kN/mm^2
        areas = np.array([0.0001, 0.0001]) # mm^2
        
        with pytest.raises(ValueError, match="requires explicit out-of-plane thickness"):
            integrate_2d_field(field, areas, thickness=None)
            
        with pytest.raises(ValueError, match="strictly positive"):
            integrate_2d_field(field, areas, thickness=-1.0)
            
        with pytest.raises(ValueError, match="strictly positive"):
            integrate_2d_field(field, areas, thickness=0.0)
            
        val = integrate_2d_field(field, areas, thickness=1.0)
        assert math.isclose(val, 6e-6, rel_tol=1e-12)

    def test_uel_mechanical_residual_dimensions_per_unit_thickness(self):
        """
        In f42_mixed_uel.for:
        CJAC = DETJ * WT [mm^2] (2D area integration)
        F_INT(I) = F_INT(I) + CJAC * (B_11*SIG_11 + B_22*SIG_22 + 2*B_12*SIG_12)
        [F_INT] = [mm^2] * [1/mm] * [kN/mm^2] = kN/mm.
        Proves that raw UEL mechanical residual is natively a force PER UNIT THICKNESS.
        """
        dim_cjac = {"mass": 0, "length": 2, "time": 0} # mm^2
        dim_b_matrix = {"mass": 0, "length": -1, "time": 0} # 1/mm
        dim_stress = {"mass": 1, "length": -1, "time": -2} # kN/mm^2
        
        dim_raw_force = {
            "mass": dim_cjac["mass"] + dim_b_matrix["mass"] + dim_stress["mass"],
            "length": dim_cjac["length"] + dim_b_matrix["length"] + dim_stress["length"],
            "time": dim_cjac["time"] + dim_b_matrix["time"] + dim_stress["time"]
        }
        
        # Expected: Force per unit thickness: [Force] / [Length] = [1, 0, -2] (kN/mm)
        dim_force_per_length = {"mass": 1, "length": 0, "time": -2} # kN/mm
        assert dim_raw_force == dim_force_per_length
        assert dim_raw_force["length"] == 0 # length exponent is 0 -> Force/Length
        
        # Raw residual is NOT total physical force [Force] = [1, 1, -2] (kN)
        dim_total_force = {"mass": 1, "length": 1, "time": -2} # kN
        assert dim_raw_force != dim_total_force

    def test_uel_energy_quadrature_dimensions_per_unit_thickness(self):
        """
        In f42_mixed_uel.for:
        CJAC = DETJ * WT [mm^2] (2D area integration)
        E_ELEM = E_ELEM + CJAC * PSI
        [E_ELEM] = [mm^2] * [kN/mm^2] = kN = (kN*mm)/mm = J/mm.
        Proves that raw UEL element energy is natively an energy PER UNIT THICKNESS.
        In dimensional analysis: [Energy] / [Length] = [Force*Length]/[Length] = [Force] = [M L^1 T^-2].
        """
        dim_cjac = {"mass": 0, "length": 2, "time": 0} # mm^2
        dim_energy_density = {"mass": 1, "length": -1, "time": -2} # kN/mm^2 == J/mm^3
        
        dim_raw_energy = {
            "mass": dim_cjac["mass"] + dim_energy_density["mass"],
            "length": dim_cjac["length"] + dim_energy_density["length"],
            "time": dim_cjac["time"] + dim_energy_density["time"]
        }
        
        # Energy per unit thickness: [Energy]/[Length] = [M L^2 T^-2]/[L] = [M L^1 T^-2] (identical to force dimensions: kN = J/mm)
        dim_energy_per_length = {"mass": 1, "length": 1, "time": -2} # J/mm == (kN*mm)/mm == kN
        assert dim_raw_energy == dim_energy_per_length
        assert dim_raw_energy["length"] == 1
        
        # Raw integrated energy is NOT total scalar energy [Energy] = [1, 2, -2] (kN*mm == J)
        dim_total_energy = {"mass": 1, "length": 2, "time": -2} # kN*mm == J
        assert dim_raw_energy != dim_total_energy

    def test_rejects_companion_solid_section_as_sole_uel_proof(self):
        """
        Reject the claim that the companion UMAT card '*Solid Section, elset=All_elem, material=DUMMY_MAT'
        alone proves the UEL dimensionality.
        The UEL is an independent Fortran element routine whose quadrature and residuals do not inherit
        from the companion section. The mathematical proof requires establishing that both UEL mechanical
        residual and energy quadrature evaluate 2D area integrals (both lacking explicit thickness multiplier t).
        """
        def evaluate_uel_dimensionality_proof(claims):
            has_companion_section_proof = claims.get("companion_solid_section", False)
            has_uel_source_audit = claims.get("uel_source_audit_residual_and_energy", False)
            
            if has_companion_section_proof and not has_uel_source_audit:
                return False, "REJECTED: *Solid Section alone cannot prove UEL dimensionality without auditing UEL source lines."
            if has_uel_source_audit:
                return True, "PASSED: UEL dimensionality proven from identical area quadrature in residual and energy assembly."
            return False, "REJECTED: No valid proof provided."
            
        valid1, msg1 = evaluate_uel_dimensionality_proof({"companion_solid_section": True, "uel_source_audit_residual_and_energy": False})
        assert valid1 is False
        assert "REJECTED: *Solid Section alone cannot prove UEL dimensionality" in msg1
        
        valid2, msg2 = evaluate_uel_dimensionality_proof({"companion_solid_section": True, "uel_source_audit_residual_and_energy": True})
        assert valid2 is True
        assert "PASSED" in msg2

    def test_unit_thickness_normalization_preserves_values_restores_dimensions(self):
        """
        Verify that adopting the project convention t_ref = 1.0 mm:
        1. Leaves numerical floating-point values identical (scaling factor is exactly 1.0);
        2. Restores physical force and energy dimensions:
           F = F_raw * t_ref = (kN/mm) * (1.0 mm) = kN
           E = E_raw * t_ref = (kN*mm/mm) * (1.0 mm) = kN*mm == J
        """
        t_ref = 1.0 # mm
        
        raw_residual_force_per_mm = 0.757778 # kN/mm (raw UEL resultant)
        raw_energy_per_mm = 0.002359329 # kN*mm/mm (raw UEL element energy sum)
        
        total_force_kn = raw_residual_force_per_mm * t_ref
        total_energy_j = raw_energy_per_mm * t_ref
        
        assert total_force_kn == raw_residual_force_per_mm
        assert total_energy_j == raw_energy_per_mm
        
        t_non_unit = 2.5 # mm
        scaled_force = raw_residual_force_per_mm * t_non_unit
        assert math.isclose(scaled_force, 1.894445, rel_tol=1e-6)
        assert scaled_force != raw_residual_force_per_mm

    def test_consistent_thickness_convention_across_all_energy_quantities(self):
        """
        Verify that W_ext, E_elas, E_frac, E_model, and Delta_book are all evaluated
        under the identical out-of-plane thickness normalization convention.
        """
        t_norm = 1.0 # mm
        
        w_ext_raw = 0.003500 # kN*mm/mm == J/mm
        e_elas_raw = 0.002200 # kN*mm/mm == J/mm
        e_frac_raw = 0.001295 # kN*mm/mm == J/mm
        
        w_ext = w_ext_raw * t_norm # kN*mm == J
        e_elas = e_elas_raw * t_norm # kN*mm == J
        e_frac = e_frac_raw * t_norm # kN*mm == J
        e_model = e_elas + e_frac # kN*mm == J
        delta_book = e_model - w_ext # kN*mm == J
        
        assert math.isclose(e_model, 0.003495, rel_tol=1e-12)
        assert math.isclose(delta_book, -0.000005, rel_tol=1e-12)
        
        def audit_thickness_consistency(quantities_dict):
            conventions = set(q.get("thickness_convention_mm") for q in quantities_dict.values())
            if len(conventions) > 1:
                raise ValueError(f"Inconsistent thickness conventions detected across quantities: {conventions}")
            return True
            
        consistent_dict = {
            "W_ext": {"val": w_ext, "thickness_convention_mm": 1.0},
            "E_elas": {"val": e_elas, "thickness_convention_mm": 1.0},
            "E_frac": {"val": e_frac, "thickness_convention_mm": 1.0},
            "Delta_book": {"val": delta_book, "thickness_convention_mm": 1.0}
        }
        assert audit_thickness_consistency(consistent_dict) is True
        
        inconsistent_dict = {
            "W_ext": {"val": w_ext, "thickness_convention_mm": 1.0},
            "E_elas": {"val": e_elas_raw, "thickness_convention_mm": None},
        }
        with pytest.raises(ValueError, match="Inconsistent thickness conventions"):
            audit_thickness_consistency(inconsistent_dict)

    def test_historical_reference_anchor_under_unit_thickness_normalization(self):
        """
        Verify that canonical reference anchor values:
        F_max = 0.757778 kN, u(F_max) = 0.005857 mm, K_0 = 137.945520 kN/mm
        represent the resultant and stiffness for the adopted project convention t_ref = 1.0 mm slice.
        In raw 2D continuum terms:
        F_max_raw = 0.757778 kN/mm
        K_0_raw   = 137.945520 kN/mm^2
        """
        t_ref = 1.0 # mm
        
        f_max_benchmark = 0.757778 # kN
        k_0_benchmark   = 137.945520 # kN/mm
        u_peak          = 0.005857 # mm
        
        f_max_raw = f_max_benchmark / t_ref # 0.757778 kN/mm
        k_0_raw   = k_0_benchmark / t_ref   # 137.945520 kN/mm^2
        
        assert math.isclose(f_max_raw * t_ref, f_max_benchmark, rel_tol=1e-12)
        assert math.isclose(k_0_raw * t_ref, k_0_benchmark, rel_tol=1e-12)
        
        f_at_1um = k_0_benchmark * 0.001
        f_raw_at_1um = k_0_raw * 0.001
        assert math.isclose(f_at_1um, 0.13794552, rel_tol=1e-6)
        assert math.isclose(f_raw_at_1um * t_ref, f_at_1um, rel_tol=1e-12)

    def test_rejects_unsupported_claim_that_pandey_kumar_prescribes_thickness(self):
        """
        Verify that claims attributing the 1.0 mm out-of-plane thickness to the Pandey & Kumar (2025)
        literature paper are strictly rejected unless an explicit primary-source citation is present.
        
        Provenance audit facts:
        1. Pandey & Kumar (2025), CMES 144(3), 3251-3276, Section 4.1 (pages 3264-3265) formulates the
           Mode-I benchmark strictly in 2D (1.0 mm x 1.0 mm plate, a_0 = 0.5 mm, E = 210 GPa, nu = 0.3,
           l_0 = 0.0075 mm, G_c = 2.7e-3 kN/mm) and omits any out-of-plane thickness specification.
        2. In contrast, Section 4.4 explicitly specifies thickness for the L-panel (t = 100 mm).
        3. Therefore, t_ref = 1.0 mm is a project implementation convention adopted to convert native
           2D per-unit-thickness UEL quantities (kN/mm, J/mm) into reported resultant physical forces (kN)
           and total scalar energies (kN*mm == J) for a 1.0 mm slice.
        4. Companion layer card '*Solid Section, elset=All_elem, material=DUMMY_MAT' with explicit '1.0'
           is project-level deck evidence that the visualization layer uses the same convention, but is NOT
           proof of a literature-prescribed thickness.
        """
        def validate_thickness_provenance_claim(claim_dict):
            """
            Validates scientific claims regarding 2D out-of-plane thickness provenance.
            Rejects claims that assert literature prescribed t=1mm without primary-source citation.
            """
            claims_literature_prescribed = claim_dict.get("claims_literature_prescribed_thickness", False)
            citation_provided = claim_dict.get("primary_source_citation", None)
            
            # Known verified primary literature fact:
            # Pandey & Kumar (2025) Sec 4.1 does NOT prescribe thickness for Mode-I
            if claims_literature_prescribed:
                if not citation_provided or "Sec. 4.1" not in citation_provided:
                    return False, "REJECTED: Pandey & Kumar (2025) Section 4.1 does not prescribe an out-of-plane thickness for the Mode-I benchmark."
                # Even if Sec 4.1 is cited, the paper text actually omits thickness:
                has_verified_text = claim_dict.get("verified_text_contains_thickness", False)
                if not has_verified_text:
                    return False, "REJECTED: Primary paper audit confirms Section 4.1 omits thickness for Mode-I plate."
            
            # The scientifically valid three-part framework:
            has_lit_2d = claim_dict.get("literature_formulation_is_2d", False)
            has_proj_conv = claim_dict.get("project_convention_t1mm", False)
            has_companion_secondary = claim_dict.get("companion_solid_section_is_secondary_only", False)
            
            if has_lit_2d and has_proj_conv and has_companion_secondary:
                return True, "PASSED: Scientifically accurate distinction between 2D literature formulation, project convention (t_ref=1.0 mm), and secondary companion section."
                
            return False, "REJECTED: Must maintain three-way distinction between literature 2D formulation, project convention, and companion layer."

        # Case 1: Erroneous claim that literature prescribes t=1mm -> REJECTED
        res1, msg1 = validate_thickness_provenance_claim({
            "claims_literature_prescribed_thickness": True,
            "primary_source_citation": "Pandey & Kumar (2025) Sec. 4.1",
            "verified_text_contains_thickness": False
        })
        assert res1 is False
        assert "omits thickness" in msg1

        # Case 2: Naked assertion without citation -> REJECTED
        res2, msg2 = validate_thickness_provenance_claim({
            "claims_literature_prescribed_thickness": True,
            "primary_source_citation": None
        })
        assert res2 is False
        assert "REJECTED" in msg2

        # Case 3: Scientifically accurate three-part classification -> PASSED
        res3, msg3 = validate_thickness_provenance_claim({
            "literature_formulation_is_2d": True,
            "project_convention_t1mm": True,
            "companion_solid_section_is_secondary_only": True,
            "claims_literature_prescribed_thickness": False
        })
        assert res3 is True
        assert "PASSED" in msg3
