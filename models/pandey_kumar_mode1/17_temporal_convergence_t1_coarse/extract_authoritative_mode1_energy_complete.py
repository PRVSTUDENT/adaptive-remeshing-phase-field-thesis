"""
Authoritative Mode-I Gate-6B Energy and Mechanical Parity Extractor
Job: PK_MODE1_T1_COARSE_ENERGY (Job 1409734.mmaster02)

Explicit Unit System:
  Length: mm
  Force:  kN
  Stress: GPa = kN/mm^2
  Native Work/Energy: kN*mm = 1.0 J
  Conversions:
    1 kN*mm = 1.0 J = 1000.0 mJ = 1.0e6 uJ (microjoules)

Extracts:
1. Complete F-u trajectory and RP reaction history.
2. Canonical initial structural stiffness K0 and R^2.
3. Peak reaction force F_max and u(F_max).
4. Frame-by-frame element-integrated SDV17 (E_frac) and SDV18 (E_elas) from Layer 3 (All_elem).
   Uses SINGLE-VALUE DEDUPLICATION per unique elementLabel to prevent 4x overcounting from CPE4 Gauss points.
5. Global energies in both native kN*mm (= J) and mJ:
   E_elas(u), E_frac(u), E_model(u) = E_elas + E_frac.
6. Cumulative external work W_ext(u) = \int_0^u F(u') du' (trapezoidal integration).
7. Canonical bookkeeping difference:
   \Delta_book(u) = E_model(u) - W_ext(u)
   \varepsilon_book(u) = |\Delta_book(u)| / max(|W_ext|, |E_model|, 1e-12) * 100%
   RelDiff_signed(u) = \Delta_book(u) / max(|W_ext|, 1e-12) * 100%
8. Mechanical parity audit against canonical reference (Job 1398090 / Job 1409577).
"""

import sys
import os
import math
import json
from odbAccess import openOdb

def linear_regression(x_vals, y_vals):
    n = len(x_vals)
    if n < 2:
        return 0.0, 0.0, 0.0
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xx = sum(x * x for x in x_vals)
    sum_yy = sum(y * y for y in y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-20:
        return 0.0, 0.0, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    
    # R^2
    ss_tot = sum((y - (sum_y / n)) ** 2 for y in y_vals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, y_vals))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-20 else 1.0
    return slope, intercept, r2

def extract_authoritative_energy(odb_path, json_out_path, job_id="1409734.mmaster02"):
    print("================================================================================")
    print("OPENING ODB: %s" % odb_path)
    print("================================================================================")
    odb = openOdb(odb_path, readOnly=True)
    
    rp_set = None
    if 'N_RP' in odb.rootAssembly.nodeSets:
        rp_set = odb.rootAssembly.nodeSets['N_RP']
    elif 'SET_RP' in odb.rootAssembly.nodeSets:
        rp_set = odb.rootAssembly.nodeSets['SET_RP']
        
    frames_data = []
    u_vals = []
    rf_vals = []
    w_ext_vals = []
    e_elas_vals = []
    e_frac_vals = []
    e_model_vals = []
    delta_book_vals = []
    eps_book_vals = []
    
    u_prev = 0.0
    rf_prev = 0.0
    w_cum = 0.0 # in kN*mm = J
    
    total_frames = sum(len(step.frames) for step in odb.steps.values())
    print("[INFO] Total frames across all steps: %d" % total_frames)
    
    processed_count = 0
    
    for step_name in sorted(odb.steps.keys()):
        step = odb.steps[step_name]
        print("\n--- Processing %s (%d frames) ---" % (step_name, len(step.frames)))
        
        for frame_idx, frame in enumerate(step.frames):
            frame_val = float(frame.frameValue)
            fkeys = frame.fieldOutputs.keys()
            
            # Extract RP U2 and RF2
            u_val = 0.0
            rf_val = 0.0
            
            if 'U' in fkeys:
                u_field = frame.fieldOutputs['U']
                if rp_set:
                    u_sub = u_field.getSubset(region=rp_set)
                    if len(u_sub.values) > 0:
                        u_val = float(u_sub.values[0].data[1])
                else:
                    for val in u_field.values:
                        if val.nodeLabel == 999999:
                            u_val = float(val.data[1])
                            break
                            
            if 'RF' in fkeys:
                rf_field = frame.fieldOutputs['RF']
                if rp_set:
                    rf_sub = rf_field.getSubset(region=rp_set)
                    if len(rf_sub.values) > 0:
                        rf_val = float(rf_sub.values[0].data[1])
                else:
                    for val in rf_field.values:
                        if val.nodeLabel == 999999:
                            rf_val = float(val.data[1])
                            break
                            
            # Integrate external work: W_ext = \int RF du (native kN*mm = J)
            if len(frames_data) > 0:
                du = u_val - u_prev
                dw = 0.5 * (rf_val + rf_prev) * du
                w_cum += dw
            else:
                w_cum = 0.5 * rf_val * u_val if u_val > 1e-12 else 0.0
            u_prev = u_val
            rf_prev = rf_val
            
            # Extract element energies from All_elem (SDV17 = E_frac, SDV18 = E_elas)
            # Both are native kN*mm = J
            e_frac_sum = 0.0
            e_elas_sum = 0.0
            has_energy_sdvs = False
            
            if 'SDV17' in fkeys and 'SDV18' in fkeys:
                has_energy_sdvs = True
                sdv17 = frame.fieldOutputs['SDV17']
                sdv18 = frame.fieldOutputs['SDV18']
                
                # Deduplicated unique element summation
                seen_elems = set()
                for v17, v18 in zip(sdv17.values, sdv18.values):
                    eid = v17.elementLabel
                    if eid not in seen_elems:
                        seen_elems.add(eid)
                        e_frac_sum += float(v17.data)
                        e_elas_sum += float(v18.data)
            elif 'SDV' in fkeys:
                # Combined SDV tensor field
                has_energy_sdvs = True
                sdv_field = frame.fieldOutputs['SDV']
                seen_elems = set()
                for val in sdv_field.values:
                    eid = val.elementLabel
                    if eid not in seen_elems:
                        seen_elems.add(eid)
                        if len(val.data) >= 18:
                            e_frac_sum += float(val.data[16]) # 0-indexed SDV17
                            e_elas_sum += float(val.data[17]) # 0-indexed SDV18
                            
            e_model = e_elas_sum + e_frac_sum if has_energy_sdvs else 0.0
            delta_book = (e_model - w_cum) if has_energy_sdvs else 0.0 # Delta_book = E_model - W_ext (kN*mm)
            denom = max(abs(w_cum), abs(e_model), 1e-12)
            eps_book = (abs(delta_book) / denom) * 100.0 if has_energy_sdvs else 0.0 # absolute normalized error (%)
            signed_reldiff_pct = (delta_book / max(abs(w_cum), 1e-12)) * 100.0 if has_energy_sdvs else 0.0
            
            frame_record = {
                "step": step_name,
                "frame_id": frame.frameId,
                "step_time": frame_val,
                "u_mm": u_val,
                "rf_kN": rf_val,
                "w_ext_kNmm": w_cum,
                "w_ext_mJ": w_cum * 1000.0,
                "e_elas_kNmm": e_elas_sum,
                "e_elas_mJ": e_elas_sum * 1000.0,
                "e_frac_kNmm": e_frac_sum,
                "e_frac_mJ": e_frac_sum * 1000.0,
                "e_model_kNmm": e_model,
                "e_model_mJ": e_model * 1000.0,
                "delta_book_kNmm": delta_book,
                "delta_book_mJ": delta_book * 1000.0,
                "signed_reldiff_pct": signed_reldiff_pct,
                "eps_book_abs_pct": eps_book,
                "has_sdvs": has_energy_sdvs
            }
            frames_data.append(frame_record)
            u_vals.append(u_val)
            rf_vals.append(rf_val)
            w_ext_vals.append(w_cum)
            if has_energy_sdvs:
                e_elas_vals.append(e_elas_sum)
                e_frac_vals.append(e_frac_sum)
                e_model_vals.append(e_model)
                delta_book_vals.append(delta_book)
                eps_book_vals.append(eps_book)
                
            processed_count += 1
            if processed_count % 500 == 0 or frame_idx == len(step.frames)-1:
                print("  Frame %4d: u=%.6f mm, RF=%.6f kN, W_ext=%.6f mJ (%.6e kN*mm), E_elas=%.6f mJ, E_frac=%.6f mJ, eps_book=%.4f%%" % (
                    processed_count, u_val, rf_val, w_cum * 1000.0, w_cum, e_elas_sum * 1000.0, e_frac_sum * 1000.0, eps_book))
                
    odb.close()
    
    # Compute Mechanical Quantities
    # Initial stiffness K0 on linear elastic range (u in [0, 0.002] mm)
    elastic_u = [u for u, rf in zip(u_vals, rf_vals) if 0.0 < u <= 0.0020]
    elastic_rf = [rf for u, rf in zip(u_vals, rf_vals) if 0.0 < u <= 0.0020]
    k0, intercept, r2 = linear_regression(elastic_u, elastic_rf)
    
    # Peak force
    f_max = max(rf_vals) if rf_vals else 0.0
    u_peak_idx = rf_vals.index(f_max) if rf_vals else 0
    u_peak = u_vals[u_peak_idx] if rf_vals else 0.0
    
    # Final state
    u_final = u_vals[-1] if u_vals else 0.0
    rf_final = rf_vals[-1] if rf_vals else 0.0
    w_final_kNmm = w_ext_vals[-1] if w_ext_vals else 0.0
    w_final_mJ = w_final_kNmm * 1000.0
    
    # Parity comparisons vs Canonical Reference (K0=137.945520, F_max=0.757778 at u=0.005857)
    k0_ref = 137.945520
    f_max_ref = 0.757778
    u_peak_ref = 0.005857
    
    delta_k0_pct = ((k0 - k0_ref) / k0_ref) * 100.0
    delta_f_max_pct = ((f_max - f_max_ref) / f_max_ref) * 100.0
    
    print("\n================================================================================")
    print("AUTHORITATIVE EXTRACTION SUMMARY")
    print("================================================================================")
    print("1. MECHANICAL PARITY:")
    print("   - Initial Stiffness K0:      %.6f kN/mm (R^2 = %.8f, N = %d)" % (k0, r2, len(elastic_u)))
    print("   - Reference Stiffness K0:    %.6f kN/mm" % k0_ref)
    print("   - Delta K0:                  %+.4f %%" % delta_k0_pct)
    print("   - Peak Reaction Force F_max: %.6f kN at u = %.6f mm" % (f_max, u_peak))
    print("   - Reference Peak Force:      %.6f kN at u = %.6f mm" % (f_max_ref, u_peak_ref))
    print("   - Delta F_max:               %+.4f %%" % delta_f_max_pct)
    print("   - Final Displacement u:      %.6f mm (Final RF = %.6f kN, W_ext = %.6f mJ = %.6e kN*mm)" % (
        u_final, rf_final, w_final_mJ, w_final_kNmm))
        
    print("\n2. GLOBAL ENERGY EVOLUTION (SIMULTANEOUS kN*mm AND mJ REPORTING):")
    if e_elas_vals and e_frac_vals:
        e_elas_final_kNmm = e_elas_vals[-1]
        e_frac_final_kNmm = e_frac_vals[-1]
        e_model_final_kNmm = e_model_vals[-1]
        delta_book_final_kNmm = delta_book_vals[-1]
        eps_book_final_pct = eps_book_vals[-1]
        signed_reldiff_final_pct = (delta_book_final_kNmm / max(abs(w_final_kNmm), 1e-12)) * 100.0
        
        print("   - Stored Elastic E_elas:   %.8e kN*mm  =  %.6f mJ  =  %.3f uJ" % (
            e_elas_final_kNmm, e_elas_final_kNmm * 1000.0, e_elas_final_kNmm * 1.0e6))
        print("   - Fracture Surface E_frac: %.8e kN*mm  =  %.6f mJ  =  %.3f uJ" % (
            e_frac_final_kNmm, e_frac_final_kNmm * 1000.0, e_frac_final_kNmm * 1.0e6))
        print("   - Total Model Energy:      %.8e kN*mm  =  %.6f mJ  =  %.3f uJ" % (
            e_model_final_kNmm, e_model_final_kNmm * 1000.0, e_model_final_kNmm * 1.0e6))
        print("   - External Work W_ext:     %.8e kN*mm  =  %.6f mJ  =  %.3f uJ" % (
            w_final_kNmm, w_final_mJ, w_final_kNmm * 1.0e6))
        print("   - Bookkeeping Diff (E-W):  %+.8e kN*mm = %+.6f mJ (Signed RelDiff = %+.4f %%)" % (
            delta_book_final_kNmm, delta_book_final_kNmm * 1000.0, signed_reldiff_final_pct))
        print("   - Absolute Normalized Err: %.4f %%" % eps_book_final_pct)
        print("   - Peak Delta Bookkeeping:  %+.8e kN*mm = %+.6f mJ" % (
            max(abs(d) for d in delta_book_vals), max(abs(d) for d in delta_book_vals) * 1000.0))
    else:
        print("   [WARNING] SDV energy fields were not present in ODB frames.")
        
    # Save structured extraction JSON
    summary_out = {
        "job_id": job_id,
        "units": {
            "length": "mm",
            "force": "kN",
            "energy_native": "kN*mm = J",
            "energy_scaled": "mJ = 1e-3 kN*mm",
            "energy_micro": "uJ = 1e-6 kN*mm"
        },
        "bookkeeping_convention": {
            "formula": "Delta_book = E_model - W_ext",
            "signed_relative_difference": "Signed_RelDiff_pct = (E_model - W_ext) / W_ext * 100%",
            "absolute_normalized_error": "eps_book_pct = |E_model - W_ext| / max(W_ext, E_model) * 100%"
        },
        "mechanical_metrics": {
            "K0_kN_per_mm": k0,
            "K0_intercept_kN": intercept,
            "K0_R2": r2,
            "K0_fit_points": len(elastic_u),
            "delta_K0_pct": delta_k0_pct,
            "F_max_kN": f_max,
            "u_at_F_max_mm": u_peak,
            "delta_F_max_pct": delta_f_max_pct,
            "u_final_mm": u_final,
            "rf_final_kN": rf_final,
            "w_ext_final_kNmm": w_final_kNmm,
            "w_ext_final_mJ": w_final_mJ
        },
        "energy_balance": {
            "has_energy_sdvs": bool(e_elas_vals),
            "e_elas_final_kNmm": e_elas_vals[-1] if e_elas_vals else None,
            "e_elas_final_mJ": e_elas_vals[-1] * 1000.0 if e_elas_vals else None,
            "e_frac_final_kNmm": e_frac_vals[-1] if e_frac_vals else None,
            "e_frac_final_mJ": e_frac_vals[-1] * 1000.0 if e_frac_vals else None,
            "e_model_final_kNmm": e_model_vals[-1] if e_model_vals else None,
            "e_model_final_mJ": e_model_vals[-1] * 1000.0 if e_model_vals else None,
            "w_ext_final_kNmm": w_final_kNmm,
            "w_ext_final_mJ": w_final_mJ,
            "delta_book_final_kNmm": delta_book_vals[-1] if delta_book_vals else None,
            "delta_book_final_mJ": delta_book_vals[-1] * 1000.0 if delta_book_vals else None,
            "signed_reldiff_final_pct": signed_reldiff_final_pct if e_elas_vals else None,
            "eps_book_final_pct": eps_book_vals[-1] if eps_book_vals else None
        },
        "frames_trajectory": frames_data
    }
    
    with open(json_out_path, 'w') as f:
        json.dump(summary_out, f, indent=2)
    print("\nSaved authoritative extraction JSON to: %s" % json_out_path)

if __name__ == '__main__':
    odb = sys.argv[1] if len(sys.argv) > 1 else 'PK_MODE1_T1_COARSE_ENERGY.odb'
    out_json = sys.argv[2] if len(sys.argv) > 2 else 'MODE1_AUTHORITATIVE_ENERGY_EVALUATION.json'
    jid = sys.argv[3] if len(sys.argv) > 3 else '1409734.mmaster02'
    extract_authoritative_energy(odb, out_json, jid)
