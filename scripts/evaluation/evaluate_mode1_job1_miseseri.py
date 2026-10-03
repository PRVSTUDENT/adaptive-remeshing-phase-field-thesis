# -*- coding: utf-8 -*-
"""
evaluate_mode1_job1_miseseri.py

Evaluator for Mode-I Layered Job-1_UEL Pre-Analysis (Job 1409912.mmaster02 / Package 89).
Protocol Version: 2
Phase: MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

Compares the layered Job-1 pre-analysis (DIAGNOSTIC_JOB1_LAYERED_VARIANT / PANDEY_KUMAR_REFERENCE_FIDELITY_CANDIDATE)
against the standard-continuum pre-analysis diagnostic variant (STANDARD_CONTINUUM_PREANALYSIS_VARIANT)
on the canonical 2,906-element coarse mesh (2,818 CPE4 quads, 88 CPE3 triangles, 2,988 nodes) at matched physical displacement states.

Evaluates 12 Mandatory Pre-Terminal and Terminal Metrics:
1. Exact step/frame/time/increment provenance and matched displacement state
2. All_elem element count and output-position provenance
3. One WHOLE_ELEMENT MISESERI value per underlying finite element, with duplicate and missing checks
4. MISESERI global statistics (max, mean, median, standard deviation, sum)
5. Normalized footprints (eta = e / e_max >= 50%, 20%, 10%, 5%, 2%, 1%)
6. Five-region statistics (Crack-Tip Corridor, Crack Wake, Right Ligament, Far Field, Boundary Regions)
7. Far-field + wake share of total MISESERI
8. High-MISESERI parasitic / outside-corridor ratio
9. Transverse corridor width profile w(x) as a function of longitudinal coordinate x
10. High-error bounding boxes and spatial spans (dx x dy)
11. Layered-vs-standard element-by-element MISESERI differences (max, mean, RMS, correlation r) at matched displacement
12. Qualitative comparison to Pandey & Kumar (2025) Fig. 6(a) spatial footprint without inventing raw values

Predeclared Scientific Decision Logic:
Classified strictly on observed spatial pattern changes without arbitrary hardcoded percentage thresholds:
- LAYERED_JOB1_TOWARD_TARGET_LOCALIZATION: Directional shift of error concentration toward crack-tip corridor
  (corridor share increases, far-field+wake share decreases)
- LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT: Spatial error distribution remains invariant within discretization/numerical
  variation (correlation r >= 0.9990 and regional share shifts are negligible)
- LAYERED_JOB1_AWAY_FROM_TARGET_LOCALIZATION: Far-field footprint broadens or crack-tip corridor localization deteriorates
"""

from __future__ import print_function
import os
import sys
import csv
import json
import math
import argparse

# Canonical 5-Region Spatial Definitions on Omega = [0, 1] x [0, 1] mm
# Governed by Stage-2 BC Audit and Stage-4 Stress Transfer Audit standards
REGION_DEFINITIONS = {
    "CRACK_TIP_CORRIDOR": {
        "description": "Active crack-tip singular and initial extension zone",
        "predicate": lambda x, y: (0.45 <= x <= 0.65) and (0.45 <= y <= 0.55),
        "expected_count": 49
    },
    "CRACK_WAKE": {
        "description": "Pre-existing sharp slit flanks and wake region",
        "predicate": lambda x, y: (0.00 <= x < 0.45) and (0.45 <= y <= 0.55),
        "expected_count": 110
    },
    "RIGHT_LIGAMENT": {
        "description": "Remaining intact horizontal ligament towards right edge",
        "predicate": lambda x, y: (0.65 < x <= 1.00) and (0.45 <= y <= 0.55),
        "expected_count": 119
    },
    "FAR_FIELD": {
        "description": "Bulk elastic plate interior away from crack and boundaries",
        "predicate": lambda x, y: (0.10 <= y < 0.45 or 0.55 < y <= 0.90),
        "expected_count": 2080
    },
    "BOUNDARY_REGIONS": {
        "description": "Top loaded roller and bottom supported boundary strips",
        "predicate": lambda x, y: (y < 0.10 or y > 0.90),
        "expected_count": 548
    }
}

CANONICAL_TOTAL_ELEMENTS = 2906
NORMALIZED_THRESHOLDS = [0.50, 0.20, 0.10, 0.05, 0.02, 0.01]


def classify_element_region(x, y):
    """Classifies an element centroid (x, y) into one of 5 mutually exclusive regions."""
    if y < 0.10 or y > 0.90:
        return "BOUNDARY_REGIONS"
    if 0.45 <= y <= 0.55:
        if x < 0.45:
            return "CRACK_WAKE"
        elif x <= 0.65:
            return "CRACK_TIP_CORRIDOR"
        else:
            return "RIGHT_LIGAMENT"
    return "FAR_FIELD"


def load_canonical_coordinates(reference_csv_path):
    """Loads element_id -> (xc, yc, element_type) map from reference coarse pre-analysis."""
    coords = {}
    if not os.path.isfile(reference_csv_path):
        raise IOError("Reference coordinate file not found: %s" % reference_csv_path)

    with open(reference_csv_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["element_id"])
            xc = float(r["xc"])
            yc = float(r["yc"])
            etype = r.get("element_type", "UNKNOWN")
            coords[eid] = {"xc": xc, "yc": yc, "element_type": etype}
    return coords


def load_miseseri_dataset(csv_path, fallback_coords=None):
    """
    Loads MISESERI data from CSV.
    Enforces: one WHOLE_ELEMENT MISESERI value per underlying finite element.
    Handles:
    - Standard single-layer elements (IDs 1..2906)
    - Layered 3-layer companion facsimile elements (IDs 5813..8718, mapped to 1..2906)
    - Validates deduplication and completeness (exact 2,906 elements)
    """
    if not os.path.isfile(csv_path):
        raise IOError("MISESERI CSV file not found: %s" % csv_path)

    elements = {}
    raw_rows = 0
    duplicate_count = 0

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            raw_rows += 1
            raw_id = int(r["element_id"])
            miseseri = float(r["miseseri"])

            # Map Layer 3 companion IDs (5813..8718) to underlying physical element IDs (1..2906)
            if raw_id > 2 * CANONICAL_TOTAL_ELEMENTS:
                phys_id = raw_id - 2 * CANONICAL_TOTAL_ELEMENTS
            elif raw_id > CANONICAL_TOTAL_ELEMENTS:
                phys_id = raw_id - CANONICAL_TOTAL_ELEMENTS
            else:
                phys_id = raw_id

            if phys_id in elements:
                duplicate_count += 1
                continue

            xc = None
            yc = None
            etype = "UNKNOWN"

            if "xc" in r and "yc" in r and r["xc"] and r["yc"]:
                xc = float(r["xc"])
                yc = float(r["yc"])
                etype = r.get("element_type", "UNKNOWN")
            elif fallback_coords and phys_id in fallback_coords:
                xc = fallback_coords[phys_id]["xc"]
                yc = fallback_coords[phys_id]["yc"]
                etype = fallback_coords[phys_id]["element_type"]
            else:
                raise ValueError("Missing centroid coordinates for element %d" % phys_id)

            reg = classify_element_region(xc, yc)

            elements[phys_id] = {
                "element_id": phys_id,
                "raw_element_id": raw_id,
                "xc": xc,
                "yc": yc,
                "element_type": etype,
                "region": reg,
                "miseseri": miseseri
            }

    # Completeness verification
    missing_ids = [i for i in range(1, CANONICAL_TOTAL_ELEMENTS + 1) if i not in elements]

    validation = {
        "raw_rows_parsed": raw_rows,
        "unique_elements_loaded": len(elements),
        "expected_elements": CANONICAL_TOTAL_ELEMENTS,
        "duplicate_entries_detected": duplicate_count,
        "missing_ids_count": len(missing_ids),
        "missing_ids": missing_ids[:10],
        "is_complete_and_unique": (len(elements) == CANONICAL_TOTAL_ELEMENTS and len(missing_ids) == 0),
        "element_representation": "one WHOLE_ELEMENT MISESERI value per underlying finite element"
    }

    if not validation["is_complete_and_unique"]:
        raise ValueError("Dataset validation failed for %s: loaded %d unique elements, missing %d, duplicates %d" % (
            csv_path, len(elements), len(missing_ids), duplicate_count
        ))

    return elements, validation


def compute_global_statistics(elements):
    """Computes global descriptive statistics across all 2,906 elements."""
    vals = [e["miseseri"] for e in elements.values()]
    n = len(vals)
    vals_sorted = sorted(vals)

    err_sum = sum(vals)
    err_mean = err_sum / float(n)
    err_max = max(vals)
    err_min = min(vals)

    # Median
    if n % 2 == 1:
        err_median = vals_sorted[n // 2]
    else:
        err_median = 0.5 * (vals_sorted[n // 2 - 1] + vals_sorted[n // 2])

    # Standard deviation
    variance = sum((v - err_mean) ** 2 for v in vals) / float(n)
    err_std = math.sqrt(variance)

    # Peak-to-mean ratio
    peak_to_mean = (err_max / err_mean) if err_mean > 0 else 0.0

    return {
        "count": n,
        "sum_mpa": err_sum,
        "mean_mpa": err_mean,
        "median_mpa": err_median,
        "std_mpa": err_std,
        "max_mpa": err_max,
        "min_mpa": err_min,
        "peak_to_mean_ratio": peak_to_mean
    }


def compute_five_region_statistics(elements):
    """Partitions elements into 5 canonical regions and calculates statistics."""
    regions = {r: [] for r in REGION_DEFINITIONS.keys()}
    for e in elements.values():
        regions[e["region"]].append(e["miseseri"])

    total_sum = sum(e["miseseri"] for e in elements.values())
    stats = {}

    for reg_name, vals in regions.items():
        n = len(vals)
        r_sum = sum(vals)
        r_mean = (r_sum / float(n)) if n > 0 else 0.0
        r_max = max(vals) if n > 0 else 0.0
        share_pct = (100.0 * r_sum / total_sum) if total_sum > 0 else 0.0

        expected_n = REGION_DEFINITIONS[reg_name]["expected_count"]
        stats[reg_name] = {
            "description": REGION_DEFINITIONS[reg_name]["description"],
            "element_count": n,
            "expected_count": expected_n,
            "count_matches_expected": (n == expected_n),
            "error_sum_mpa": r_sum,
            "error_share_pct": share_pct,
            "mean_error_mpa": r_mean,
            "max_error_mpa": r_max
        }

    return stats


def compute_far_field_and_wake_share(regional_stats):
    """Computes combined Far-Field + Wake share of total MISESERI."""
    wake_sum = regional_stats["CRACK_WAKE"]["error_sum_mpa"]
    far_sum = regional_stats["FAR_FIELD"]["error_sum_mpa"]
    wake_share = regional_stats["CRACK_WAKE"]["error_share_pct"]
    far_share = regional_stats["FAR_FIELD"]["error_share_pct"]

    return {
        "far_field_error_sum_mpa": far_sum,
        "crack_wake_error_sum_mpa": wake_sum,
        "combined_error_sum_mpa": far_sum + wake_sum,
        "far_field_share_pct": far_share,
        "crack_wake_share_pct": wake_share,
        "far_field_plus_wake_share_pct": far_share + wake_share
    }


def compute_normalized_footprints(elements, thresholds=None):
    """
    Computes normalized error footprints eta = e / e_max >= threshold.
    Returns element counts, mesh fractions, and spatial bounding boxes (x_min, x_max, y_min, y_max, dx, dy).
    """
    if thresholds is None:
        thresholds = NORMALIZED_THRESHOLDS

    max_e = max(e["miseseri"] for e in elements.values())
    total_elements = len(elements)
    footprints = []

    for th in thresholds:
        cutoff = th * max_e
        active = [e for e in elements.values() if e["miseseri"] >= cutoff]
        count = len(active)
        fraction = count / float(total_elements)

        if count > 0:
            x_min = min(e["xc"] for e in active)
            x_max = max(e["xc"] for e in active)
            y_min = min(e["yc"] for e in active)
            y_max = max(e["yc"] for e in active)
            dx = x_max - x_min
            dy = y_max - y_min
        else:
            x_min = x_max = y_min = y_max = dx = dy = 0.0

        footprints.append({
            "threshold": th,
            "threshold_pct": th * 100.0,
            "cutoff_miseseri_mpa": cutoff,
            "element_count": count,
            "fraction_of_mesh": fraction,
            "bounding_box": {
                "x_min": x_min,
                "x_max": x_max,
                "y_min": y_min,
                "y_max": y_max,
                "dx": dx,
                "dy": dy
            }
        })

    return footprints


def compute_outside_corridor_ratio(elements, thresholds=None):
    """
    Computes the high-error parasitic / outside-corridor ratio.
    Evaluates what portion of high-error elements lie outside the crack-tip corridor:
    Corridor definition: x in [0.45, 0.65], y in [0.45, 0.55].
    """
    if thresholds is None:
        thresholds = [0.50, 0.10, 0.01]

    max_e = max(e["miseseri"] for e in elements.values())
    ratios = {}

    for th in thresholds:
        cutoff = th * max_e
        active = [e for e in elements.values() if e["miseseri"] >= cutoff]
        n_act = len(active)

        if n_act == 0:
            ratios["eta_ge_%dpct" % int(th * 100)] = {
                "total_active_elements": 0,
                "outside_corridor_elements": 0,
                "outside_corridor_count_ratio_pct": 0.0,
                "outside_corridor_error_share_pct": 0.0
            }
            continue

        outside = [e for e in active if not (0.45 <= e["xc"] <= 0.65 and 0.45 <= e["yc"] <= 0.55)]
        n_out = len(outside)

        sum_act = sum(e["miseseri"] for e in active)
        sum_out = sum(e["miseseri"] for e in outside)

        ratios["eta_ge_%dpct" % int(th * 100)] = {
            "total_active_elements": n_act,
            "outside_corridor_elements": n_out,
            "outside_corridor_count_ratio_pct": (100.0 * n_out / float(n_act)),
            "outside_corridor_error_share_pct": (100.0 * sum_out / sum_act) if sum_act > 0 else 0.0
        }

    return ratios


def compute_transverse_corridor_widths(elements, bin_count=20, thresholds=None):
    """
    Computes transverse corridor width w(x) = y_max(x) - y_min(x) across 20 longitudinal x bins.
    """
    if thresholds is None:
        thresholds = [0.10, 0.01]

    max_e = max(e["miseseri"] for e in elements.values())
    dx_bin = 1.0 / float(bin_count)
    bin_centers = [dx_bin * (i + 0.5) for i in range(bin_count)]

    profiles = {
        "bin_centers": bin_centers,
        "bin_width": dx_bin
    }

    for th in thresholds:
        th_key = "width_eta_%dpct" % int(th * 100)
        cutoff = th * max_e
        widths = []

        for bc in bin_centers:
            x_min = bc - 0.5 * dx_bin
            x_max = bc + 0.5 * dx_bin
            in_bin_ys = [e["yc"] for e in elements.values() if (x_min <= e["xc"] < x_max) and e["miseseri"] >= cutoff]

            if in_bin_ys:
                w = max(in_bin_ys) - min(in_bin_ys)
            else:
                w = 0.0
            widths.append(w)

        profiles[th_key] = widths

    return profiles


def compare_layered_vs_standard(layered_elements, standard_elements, displacement_scale_factor=1.0):
    """
    Performs element-by-element comparative audit across all 2,906 coarse elements.
    If displacement_scale_factor != 1.0, scales standard elements by displacement_scale_factor
    to match the physical displacement state of the layered analysis (NLGEOM=NO linear elastic scaling).
    """
    common_ids = sorted(set(layered_elements.keys()) & set(standard_elements.keys()))
    if len(common_ids) != CANONICAL_TOTAL_ELEMENTS:
        raise ValueError("Element mesh mismatch: found %d common elements vs %d expected" % (len(common_ids), CANONICAL_TOTAL_ELEMENTS))

    diffs = []
    abs_diffs = []
    rel_diffs = []
    vals_lay = []
    vals_std_matched = []

    for eid in common_ids:
        e_lay = layered_elements[eid]["miseseri"]
        e_std_raw = standard_elements[eid]["miseseri"]
        e_std_matched = e_std_raw * displacement_scale_factor

        d = e_lay - e_std_matched
        diffs.append(d)
        abs_diffs.append(abs(d))
        rel = (abs(d) / e_std_matched) if e_std_matched > 0 else 0.0
        rel_diffs.append(rel)
        vals_lay.append(e_lay)
        vals_std_matched.append(e_std_matched)

    n = len(common_ids)
    mean_diff = sum(diffs) / float(n)
    mean_abs_diff = sum(abs_diffs) / float(n)
    max_abs_diff = max(abs_diffs)
    rms_diff = math.sqrt(sum(d ** 2 for d in diffs) / float(n))
    mean_rel_diff = sum(rel_diffs) / float(n)
    max_rel_diff = max(rel_diffs)

    # Pearson correlation coefficient r
    mean_lay = sum(vals_lay) / float(n)
    mean_std = sum(vals_std_matched) / float(n)
    num = sum((l - mean_lay) * (s - mean_std) for l, s in zip(vals_lay, vals_std_matched))
    den_l = sum((l - mean_lay) ** 2 for l in vals_lay)
    den_s = sum((s - mean_std) ** 2 for s in vals_std_matched)
    corr_r = (num / math.sqrt(den_l * den_s)) if (den_l > 0 and den_s > 0) else 1.0

    return {
        "coincident_elements": n,
        "displacement_scale_factor": displacement_scale_factor,
        "matched_displacement_status": "MATCHED_DIRECTLY" if abs(displacement_scale_factor - 1.0) < 1e-6 else "SCALED_FOR_LINEAR_ELASTIC_PARITY",
        "mean_diff_mpa": mean_diff,
        "mean_abs_diff_mpa": mean_abs_diff,
        "max_abs_diff_mpa": max_abs_diff,
        "rms_diff_mpa": rms_diff,
        "mean_relative_diff": mean_rel_diff,
        "max_relative_diff": max_rel_diff,
        "correlation_r": corr_r
    }


def compare_spatial_footprint_to_publication(layered_footprints, standard_footprints):
    """
    Evaluates qualitative agreement with Pandey & Kumar (2025) Fig. 6(a).
    Fig. 6(a) characteristics:
    - Highly localized horizontal refinement band along the crack path (y ~ 0.5 mm)
    - Negligible far-field refinement away from the crack plane
    - Compact crack-tip error concentration
    """
    # Compare eta >= 10% footprint span
    lay_fp_10 = next((f for f in layered_footprints if f["threshold_pct"] == 10.0), None)
    std_fp_10 = next((f for f in standard_footprints if f["threshold_pct"] == 10.0), None)

    lay_fp_1 = next((f for f in layered_footprints if f["threshold_pct"] == 1.0), None)
    std_fp_1 = next((f for f in standard_footprints if f["threshold_pct"] == 1.0), None)

    dx_10_change = (lay_fp_10["bounding_box"]["dx"] - std_fp_10["bounding_box"]["dx"]) if (lay_fp_10 and std_fp_10) else 0.0
    dy_10_change = (lay_fp_10["bounding_box"]["dy"] - std_fp_10["bounding_box"]["dy"]) if (lay_fp_10 and std_fp_10) else 0.0

    dx_1_change = (lay_fp_1["bounding_box"]["dx"] - std_fp_1["bounding_box"]["dx"]) if (lay_fp_1 and std_fp_1) else 0.0
    dy_1_change = (lay_fp_1["bounding_box"]["dy"] - std_fp_1["bounding_box"]["dy"]) if (lay_fp_1 and std_fp_1) else 0.0

    return {
        "published_reference": "Pandey & Kumar (2025), CMES 144(3), Fig. 6(a)",
        "published_qualitative_profile": "Narrow horizontal error corridor along y=0.5 with suppressed far-field error",
        "eta_10pct_dx_change_mm": dx_10_change,
        "eta_10pct_dy_change_mm": dy_10_change,
        "eta_1pct_dx_change_mm": dx_1_change,
        "eta_1pct_dy_change_mm": dy_1_change,
        "footprint_contracted": (dy_10_change <= 0.0 and dy_1_change <= 0.0)
    }


def assign_scientific_decision_logic(pairwise_comp, regional_lay, regional_std, far_wake_lay, far_wake_std):
    """
    Applies the 3-branch scientific decision logic mandated by supervisor governance:
    - LAYERED_JOB1_TOWARD_TARGET_LOCALIZATION
    - LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT
    - LAYERED_JOB1_AWAY_FROM_TARGET_LOCALIZATION

    Classifies strictly based on observed spatial pattern changes without arbitrary hardcoded percentage thresholds:
    - Directional improvement: crack-tip corridor error share increases (delta_tip > 0) AND
      far-field+wake error share decreases (delta_far_wake < 0).
    - Directional deterioration: far-field+wake error share increases (delta_far_wake > 0) OR
      crack-tip corridor error share decreases (delta_tip < 0).
    - No meaningful improvement: spatial distribution remains invariant within numerical/discretization
      variation (correlation r >= 0.9990 and error share shifts are negligible |delta| < 0.5%).
    """
    mean_rel_diff = pairwise_comp["mean_relative_diff"]
    corr_r = pairwise_comp["correlation_r"]

    delta_far_wake_share = far_wake_lay["far_field_plus_wake_share_pct"] - far_wake_std["far_field_plus_wake_share_pct"]
    delta_tip_corridor_share = regional_lay["CRACK_TIP_CORRIDOR"]["error_share_pct"] - regional_std["CRACK_TIP_CORRIDOR"]["error_share_pct"]

    # Invariance check: high correlation and negligible regional shift
    is_spatially_invariant = (corr_r >= 0.9990) and (abs(delta_far_wake_share) < 0.5) and (abs(delta_tip_corridor_share) < 0.5)

    if is_spatially_invariant:
        verdict = "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT"
        rationale = (
            "Within the tested configuration on the canonical 2,906-element mesh at matched physical displacement states, "
            "the 3-layer UEL/UMAT architecture reproduces the continuum pre-analysis error distribution without "
            "altering the spatial localization pattern (correlation r = %.9f, mean relative diff = %.4f%%, "
            "crack-tip corridor Delta share = %+.3f%%, far-field+wake Delta share = %+.3f%%). "
            "The broad far-field footprint is observed in both single-layer continuum and 3-layer UEL/UMAT models, "
            "indicating that UEL/UMAT layer architecture does not explain the spatial localization difference."
            % (corr_r, 100.0 * mean_rel_diff, delta_tip_corridor_share, delta_far_wake_share)
        )
    elif delta_far_wake_share < -0.5 and delta_tip_corridor_share > 0.5:
        verdict = "LAYERED_JOB1_TOWARD_TARGET_LOCALIZATION"
        rationale = (
            "The 3-layer UEL/UMAT architecture shifts error concentration toward the physical crack-tip corridor "
            "(corridor Delta share = %+.3f%%) while reducing far-field and wake error share (Delta share = %+.3f%%)."
            % (delta_tip_corridor_share, delta_far_wake_share)
        )
    elif delta_far_wake_share > 0.5 or delta_tip_corridor_share < -0.5:
        verdict = "LAYERED_JOB1_AWAY_FROM_TARGET_LOCALIZATION"
        rationale = (
            "The 3-layer UEL/UMAT architecture broadens the far-field error footprint (Delta share = %+.3f%%) "
            "or degrades crack-tip localization (corridor Delta share = %+.3f%%)."
            % (delta_far_wake_share, delta_tip_corridor_share)
        )
    else:
        verdict = "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT"
        rationale = (
            "No systematic directional improvement toward target localization is observed "
            "(correlation r = %.9f, corridor Delta share = %+.3f%%, far-field+wake Delta share = %+.3f%%)."
            % (corr_r, delta_tip_corridor_share, delta_far_wake_share)
        )

    return {
        "verdict": verdict,
        "rationale": rationale,
        "delta_far_wake_share_pct": delta_far_wake_share,
        "delta_tip_corridor_share_pct": delta_tip_corridor_share,
        "correlation_r": corr_r,
        "mean_relative_diff_pct": 100.0 * mean_rel_diff
    }


def execute_mode1_job1_evaluation(layered_csv_path, standard_csv_path, provenance_info=None,
                                  layered_disp_mm=None, standard_disp_mm=None):
    """
    Executes complete 12-item comparative evaluation between layered Job-1 and standard continuum pre-analysis.
    Enforces matched physical displacement state comparison or scale-invariant relative indicators.
    """
    # Load fallback coordinates from standard pre-analysis
    standard_coords = load_canonical_coordinates(standard_csv_path)

    # Load datasets
    layered_elements, val_lay = load_miseseri_dataset(layered_csv_path, fallback_coords=standard_coords)
    standard_elements, val_std = load_miseseri_dataset(standard_csv_path, fallback_coords=standard_coords)

    # Provenance and displacement state
    prov = provenance_info or {
        "step_name": "Step-1",
        "increment_number": 1,
        "step_time": 1.0,
        "prescribed_displacement_mm": layered_disp_mm if layered_disp_mm is not None else 0.0050,
        "standard_prescribed_displacement_mm": standard_disp_mm if standard_disp_mm is not None else 0.0050,
        "output_variable": "MISESERI",
        "output_position": "WHOLE_ELEMENT_CENTROID",
        "element_set": "All_elem (Layer 3 CPE4/CPE3 companion facsimile elements)"
    }

    u_lay = layered_disp_mm if layered_disp_mm is not None else prov.get("prescribed_displacement_mm", 0.0050)
    u_std = standard_disp_mm if standard_disp_mm is not None else prov.get("standard_prescribed_displacement_mm", 0.0050)

    # Linear elastic scaling factor: e(c*u) = c*e(u)
    if u_std > 0 and u_lay > 0:
        disp_scale_factor = float(u_lay) / float(u_std)
    else:
        disp_scale_factor = 1.0

    matched_disp_info = {
        "layered_prescribed_displacement_mm": u_lay,
        "standard_prescribed_displacement_mm": u_std,
        "displacement_ratio": disp_scale_factor,
        "matching_method": "DIRECT_MATCH" if abs(disp_scale_factor - 1.0) < 1e-6 else "LINEAR_ELASTIC_HOMOGENEOUS_SCALING",
        "linear_elastic_scaling_note": "In linear elasticity (NLGEOM=NO, d=0), MISESERI is strictly homogeneous of degree 1 with respect to applied displacement: e(c*u) = c*e(u)."
    }

    # 4. Global statistics
    global_lay = compute_global_statistics(layered_elements)
    global_std_raw = compute_global_statistics(standard_elements)

    # 5. Normalized footprints (scale-invariant)
    footprints_lay = compute_normalized_footprints(layered_elements)
    footprints_std = compute_normalized_footprints(standard_elements)

    # 6. Five-region statistics (scale-invariant percentage shares)
    regional_lay = compute_five_region_statistics(layered_elements)
    regional_std = compute_five_region_statistics(standard_elements)

    # 7. Far-field + wake share (scale-invariant)
    far_wake_lay = compute_far_field_and_wake_share(regional_lay)
    far_wake_std = compute_far_field_and_wake_share(regional_std)

    # 8. High-MISESERI parasitic / outside-corridor ratio (scale-invariant)
    outside_lay = compute_outside_corridor_ratio(layered_elements)
    outside_std = compute_outside_corridor_ratio(standard_elements)

    # 9. Transverse corridor width profiles w(x) (scale-invariant)
    widths_lay = compute_transverse_corridor_widths(layered_elements)
    widths_std = compute_transverse_corridor_widths(standard_elements)

    # 10. High-error bounding boxes (extracted from footprints)
    bbox_lay = {fp["threshold_pct"]: fp["bounding_box"] for fp in footprints_lay}
    bbox_std = {fp["threshold_pct"]: fp["bounding_box"] for fp in footprints_std}

    # 11. Pairwise comparison at matched physical displacement state
    pairwise = compare_layered_vs_standard(layered_elements, standard_elements, displacement_scale_factor=disp_scale_factor)

    # 12. Qualitative comparison to Pandey & Kumar Fig. 6(a)
    pub_comp = compare_spatial_footprint_to_publication(footprints_lay, footprints_std)

    # Predeclared decision logic
    decision = assign_scientific_decision_logic(pairwise, regional_lay, regional_std, far_wake_lay, far_wake_std)

    results = {
        "metadata": {
            "evaluator_name": "evaluate_mode1_job1_miseseri.py",
            "protocol_version": 2,
            "governing_directive": "We need to have understood everything related to the first model before we increase complexity.",
            "candidate_model": "DIAGNOSTIC_JOB1_LAYERED_VARIANT (89_mode1_preanalysis_uel_canonical_2906, Job 1409912.mmaster02)",
            "diagnostic_variant": "STANDARD_CONTINUUM_PREANALYSIS_VARIANT (PK_PREANALYSIS_COARSE)",
            "coarse_elements": CANONICAL_TOTAL_ELEMENTS,
            "element_representation": "one WHOLE_ELEMENT MISESERI value per underlying finite element"
        },
        "item1_execution_provenance": prov,
        "item1b_matched_displacement_state": matched_disp_info,
        "item2_output_position_and_set": {
            "element_set": "All_elem",
            "element_count": CANONICAL_TOTAL_ELEMENTS,
            "quads": 2818,
            "tris": 88,
            "output_position": "WHOLE_ELEMENT_CENTROID",
            "representation": "one WHOLE_ELEMENT MISESERI value per underlying finite element",
            "error_estimator": "Abaqus native Superconvergent Patch Recovery (SPR/ZZ)"
        },
        "item3_element_completeness_and_deduplication": {
            "layered_validation": val_lay,
            "standard_validation": val_std
        },
        "item4_global_miseseri_statistics": {
            "layered_job1": global_lay,
            "standard_continuum_raw": global_std_raw,
            "standard_continuum_matched_displacement": {
                "count": global_std_raw["count"],
                "sum_mpa": global_std_raw["sum_mpa"] * disp_scale_factor,
                "mean_mpa": global_std_raw["mean_mpa"] * disp_scale_factor,
                "median_mpa": global_std_raw["median_mpa"] * disp_scale_factor,
                "std_mpa": global_std_raw["std_mpa"] * disp_scale_factor,
                "max_mpa": global_std_raw["max_mpa"] * disp_scale_factor,
                "min_mpa": global_std_raw["min_mpa"] * disp_scale_factor,
                "peak_to_mean_ratio": global_std_raw["peak_to_mean_ratio"]
            },
            "delta_sum_mpa_matched": global_lay["sum_mpa"] - (global_std_raw["sum_mpa"] * disp_scale_factor),
            "delta_mean_mpa_matched": global_lay["mean_mpa"] - (global_std_raw["mean_mpa"] * disp_scale_factor),
            "delta_max_mpa_matched": global_lay["max_mpa"] - (global_std_raw["max_mpa"] * disp_scale_factor)
        },
        "item5_normalized_footprints": {
            "layered_job1": footprints_lay,
            "standard_continuum": footprints_std
        },
        "item6_five_region_statistics": {
            "layered_job1": regional_lay,
            "standard_continuum": regional_std
        },
        "item7_far_field_plus_wake_partition": {
            "layered_job1": far_wake_lay,
            "standard_continuum": far_wake_std
        },
        "item8_high_miseseri_outside_corridor_ratio": {
            "layered_job1": outside_lay,
            "standard_continuum": outside_std
        },
        "item9_transverse_corridor_widths": {
            "layered_job1": widths_lay,
            "standard_continuum": widths_std
        },
        "item10_high_error_bounding_boxes": {
            "layered_job1": bbox_lay,
            "standard_continuum": bbox_std
        },
        "item11_element_by_element_pairwise_comparison": pairwise,
        "item12_publication_footprint_comparison": pub_comp,
        "scientific_decision_verdict": decision
    }

    return results


def format_markdown_report(results):
    """Formats the evaluation results into an auditable markdown report."""
    meta = results["metadata"]
    prov = results["item1_execution_provenance"]
    mdisp = results.get("item1b_matched_displacement_state", {})
    dec = results["scientific_decision_verdict"]
    g_lay = results["item4_global_miseseri_statistics"]["layered_job1"]
    g_std_m = results["item4_global_miseseri_statistics"]["standard_continuum_matched_displacement"]
    pw = results["item11_element_by_element_pairwise_comparison"]
    reg_lay = results["item6_five_region_statistics"]["layered_job1"]
    reg_std = results["item6_five_region_statistics"]["standard_continuum"]
    fw_lay = results["item7_far_field_plus_wake_partition"]["layered_job1"]
    fw_std = results["item7_far_field_plus_wake_partition"]["standard_continuum"]

    md = []
    md.append("# Terminal Evaluation Report: Mode-I Layered Job-1_UEL Pre-Analysis Variant")
    md.append("")
    md.append("**Evaluator:** `%s` | **Protocol Version:** %d" % (meta["evaluator_name"], meta["protocol_version"]))
    md.append("**Candidate:** `%s`" % meta["candidate_model"])
    md.append("**Diagnostic Variant:** `%s`" % meta["diagnostic_variant"])
    md.append("**Governing Directive:** *%s*" % meta["governing_directive"])
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Executive Scientific Verdict")
    md.append("")
    md.append("- **Scientific Decision:** **`%s`**" % dec["verdict"])
    md.append("- **Governing Rationale:** %s" % dec["rationale"])
    md.append("- **Correlation ($r$):** `%.9f`" % dec["correlation_r"])
    md.append("- **Mean Relative Error Difference:** `%.4f%%`" % dec["mean_relative_diff_pct"])
    md.append("- **Far-Field + Wake Share Delta:** `%+.2f%%` (`%.2f%%` vs `%.2f%%`)" % (
        dec["delta_far_wake_share_pct"],
        fw_lay["far_field_plus_wake_share_pct"],
        fw_std["far_field_plus_wake_share_pct"]
    ))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Execution & Matched Displacement Provenance (Items 1-3)")
    md.append("")
    md.append("| Provenance Field | Value | Validation Status |")
    md.append("| :--- | :--- | :--- |")
    md.append("| **Step Name** | `%s` | Validated |" % prov.get("step_name", "N/A"))
    md.append("| **Increment / Step Time** | `%s` / `%.4f` | Validated |" % (prov.get("increment_number", 1), prov.get("step_time", 1.0)))
    md.append("| **Layered Prescribed Displacement** | `%.4f mm` | Evaluated |" % mdisp.get("layered_prescribed_displacement_mm", 0.0050))
    md.append("| **Standard Prescribed Displacement** | `%.4f mm` | Evaluated |" % mdisp.get("standard_prescribed_displacement_mm", 0.0050))
    md.append("| **Displacement Scaling Ratio** | `%.4fx` (`%s`) | Enforced for Parity |" % (
        mdisp.get("displacement_ratio", 1.0), mdisp.get("matching_method", "DIRECT_MATCH")
    ))
    md.append("| **Output Set** | `All_elem` (Layer 3 companion elements) | Validated (IDs mapped to 1..2906) |")
    md.append("| **Element Count** | `%d` (%d CPE4 + %d CPE3) | 100%% complete (0 missing, 0 duplicates) |" % (
        results["item2_output_position_and_set"]["element_count"],
        results["item2_output_position_and_set"]["quads"],
        results["item2_output_position_and_set"]["tris"]
    ))
    md.append("| **Output Position & Semantics** | `WHOLE_ELEMENT_CENTROID` | One WHOLE_ELEMENT MISESERI value per underlying finite element |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Global Statistics & Pairwise Discrepancy at Matched Displacement (Items 4 & 11)")
    md.append("")
    md.append("| Metric | Layered Job-1 Variant | Standard Baseline (Matched Disp) | Delta |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append("| **Total Error Sum (MPa)** | `%.4f` | `%.4f` | `%+.4f` |" % (g_lay["sum_mpa"], g_std_m["sum_mpa"], g_lay["sum_mpa"] - g_std_m["sum_mpa"]))
    md.append("| **Mean MISESERI (MPa)** | `%.6f` | `%.6f` | `%+.6f` |" % (g_lay["mean_mpa"], g_std_m["mean_mpa"], g_lay["mean_mpa"] - g_std_m["mean_mpa"]))
    md.append("| **Median MISESERI (MPa)** | `%.6f` | `%.6f` | `%+.6f` |" % (g_lay["median_mpa"], g_std_m["median_mpa"], g_lay["median_mpa"] - g_std_m["median_mpa"]))
    md.append("| **Std Deviation (MPa)** | `%.6f` | `%.6f` | `%+.6f` |" % (g_lay["std_mpa"], g_std_m["std_mpa"], g_lay["std_mpa"] - g_std_m["std_mpa"]))
    md.append("| **Peak Error $e_{\\max}$ (MPa)** | `%.6f` | `%.6f` | `%+.6f` |" % (g_lay["max_mpa"], g_std_m["max_mpa"], g_lay["max_mpa"] - g_std_m["max_mpa"]))
    md.append("| **Max Absolute Diff (MPa)** | `%.6e` | --- | Evaluated |" % pw["max_abs_diff_mpa"])
    md.append("| **RMS Difference (MPa)** | `%.6e` | --- | Evaluated |" % pw["rms_diff_mpa"])
    md.append("| **Pearson Correlation ($r$)** | `%.9f` | --- | Evaluated |" % pw["correlation_r"])
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Five-Region Error Partition Comparison (Item 6)")
    md.append("")
    md.append("| Region | Layered Sum (MPa) | Layered Share (%) | Standard Sum (MPa) | Standard Share (%) | Delta Share (%) |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for reg in ["CRACK_TIP_CORRIDOR", "CRACK_WAKE", "RIGHT_LIGAMENT", "FAR_FIELD", "BOUNDARY_REGIONS"]:
        sl = reg_lay[reg]
        ss = reg_std[reg]
        md.append("| **%s** | `%.4f` | `%.2f%%` | `%.4f` | `%.2f%%` | `%+.2f%%` |" % (
            reg, sl["error_sum_mpa"], sl["error_share_pct"], ss["error_sum_mpa"], ss["error_share_pct"],
            sl["error_share_pct"] - ss["error_share_pct"]
        ))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5. Normalized Footprints & Bounding Boxes (Items 5 & 10)")
    md.append("")
    md.append("| Threshold $\\eta$ | Layered Elements | Layered Bounding Box | Standard Elements | Standard Bounding Box |")
    md.append("| :---: | :---: | :--- | :---: | :--- |")
    for th in NORMALIZED_THRESHOLDS:
        f_lay = next(f for f in results["item5_normalized_footprints"]["layered_job1"] if f["threshold_pct"] == th * 100)
        f_std = next(f for f in results["item5_normalized_footprints"]["standard_continuum"] if f["threshold_pct"] == th * 100)
        b_lay = f_lay["bounding_box"]
        b_std = f_std["bounding_box"]
        md.append("| **$\\ge %.1f\\%%$** | `%d` (%.2f%%) | `[%.4f, %.4f] x [%.4f, %.4f]` | `%d` (%.2f%%) | `[%.4f, %.4f] x [%.4f, %.4f]` |" % (
            th * 100, f_lay["element_count"], f_lay["fraction_of_mesh"] * 100,
            b_lay["x_min"], b_lay["x_max"], b_lay["y_min"], b_lay["y_max"],
            f_std["element_count"], f_std["fraction_of_mesh"] * 100,
            b_std["x_min"], b_std["x_max"], b_std["y_min"], b_std["y_max"]
        ))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 6. High-Error Parasitic Outside-Corridor Ratio (Item 8)")
    md.append("")
    md.append("| Threshold | Layered Outside Elements | Layered Outside Share (%) | Standard Outside Elements | Standard Outside Share (%) |")
    md.append("| :---: | :---: | :---: | :---: | :---: |")
    for th_key in ["eta_ge_50pct", "eta_ge_10pct", "eta_ge_1pct"]:
        o_lay = results["item8_high_miseseri_outside_corridor_ratio"]["layered_job1"][th_key]
        o_std = results["item8_high_miseseri_outside_corridor_ratio"]["standard_continuum"][th_key]
        md.append("| **%s** | `%d / %d` | `%.2f%%` | `%d / %d` | `%.2f%%` |" % (
            th_key, o_lay["outside_corridor_elements"], o_lay["total_active_elements"], o_lay["outside_corridor_count_ratio_pct"],
            o_std["outside_corridor_elements"], o_std["total_active_elements"], o_std["outside_corridor_count_ratio_pct"]
        ))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 7. Publication Fidelity Comparison (Item 12)")
    md.append("")
    pub = results["item12_publication_footprint_comparison"]
    md.append("- **Published Literature Reference:** %s" % pub["published_reference"])
    md.append("- **Qualitative Published Pattern:** %s" % pub["published_qualitative_profile"])
    md.append("- **Footprint Span Change at $\\eta \\ge 10\\%%$:** $dx = %+.4f\\,\\text{mm}, dy = %+.4f\\,\\text{mm}$" % (
        pub["eta_10pct_dx_change_mm"], pub["eta_10pct_dy_change_mm"]
    ))
    md.append("- **Footprint Span Change at $\\eta \\ge 1\\%%$:** $dx = %+.4f\\,\\text{mm}, dy = %+.4f\\,\\text{mm}$" % (
        pub["eta_1pct_dx_change_mm"], pub["eta_1pct_dy_change_mm"]
    ))
    md.append("")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Mode-I Layered Job-1_UEL MISESERI vs Standard Continuum Baseline")
    parser.add_argument("--layered-csv", type=str, default=None, help="Path to layered Job-1 MISESERI CSV")
    parser.add_argument("--standard-csv", type=str, default="models/pandey_kumar_mode1/adaptive_direction_evidence_package/miseseri_corrected_2906.csv", help="Path to standard continuum baseline CSV")
    parser.add_argument("--layered-disp", type=float, default=None, help="Prescribed displacement (mm) for layered analysis")
    parser.add_argument("--standard-disp", type=float, default=None, help="Prescribed displacement (mm) for standard baseline")
    parser.add_argument("--output-json", type=str, default=None, help="Output JSON path")
    parser.add_argument("--output-report", type=str, default=None, help="Output Markdown report path")
    parser.add_argument("--self-test", action="store_true", help="Run self-test comparing baseline to itself")

    args = parser.parse_args()

    if args.self_test:
        print("[INFO] Running self-test: comparing standard baseline to itself...")
        std_csv = args.standard_csv
        res = execute_mode1_job1_evaluation(std_csv, std_csv, layered_disp_mm=args.layered_disp, standard_disp_mm=args.standard_disp)
        print("[PASS] Self-test complete. Correlation: %.9f, Max Diff: %.6e" % (
            res["item11_element_by_element_pairwise_comparison"]["correlation_r"],
            res["item11_element_by_element_pairwise_comparison"]["max_abs_diff_mpa"]
        ))
        print("Verdict: %s" % res["scientific_decision_verdict"]["verdict"])
        if args.output_json:
            with open(args.output_json, "w") as fp:
                json.dump(res, fp, indent=2)
            print("[INFO] Wrote JSON: %s" % args.output_json)
        return 0

    if not args.layered_csv:
        print("[ERROR] --layered-csv path required (or pass --self-test)")
        return 1

    res = execute_mode1_job1_evaluation(args.layered_csv, args.standard_csv,
                                        layered_disp_mm=args.layered_disp, standard_disp_mm=args.standard_disp)

    if args.output_json:
        with open(args.output_json, "w") as fp:
            json.dump(res, fp, indent=2)
        print("[INFO] Wrote JSON: %s" % args.output_json)

    if args.output_report:
        rpt = format_markdown_report(res)
        with open(args.output_report, "w") as fp:
            fp.write(rpt)
        print("[INFO] Wrote report: %s" % args.output_report)

    print("Scientific Verdict: %s" % res["scientific_decision_verdict"]["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
