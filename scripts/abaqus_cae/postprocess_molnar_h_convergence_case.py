# Abaqus/CAE noGUI postprocessing for one Molnar lc015 h-convergence case.
# Run with: abaqus cae noGUI=postprocess_molnar_h_convergence_case.py -- <odb> <outdir> <case_id>
#
# Do not run with system Python. Requires Abaqus Python / Abaqus CAE.

from __future__ import annotations

import csv
import json
import os
import sys


def _args():
    # Abaqus places user args after '--'
    if "--" in sys.argv:
        idx = sys.argv.index("--")
        args = sys.argv[idx + 1 :]
    else:
        args = [a for a in sys.argv[1:] if not a.endswith(".py")]
    if len(args) < 3:
        raise RuntimeError("Usage: abaqus cae noGUI=script.py -- <odb> <outdir> <case_id>")
    return args[0], args[1], args[2]


def main():
    odb_path, outdir, case_id = _args()
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    from abaqus import session  # type: ignore
    from abaqusConstants import OFF, PNG, LANDSCAPE  # type: ignore
    from odbAccess import openOdb  # type: ignore

    odb = openOdb(path=odb_path, readOnly=True)
    # Prefer RP nset history if present; otherwise assemble RF2/U2 from frames.
    step_names = list(odb.steps.keys())
    rows = []
    # Explicit origin
    rows.append({"step": "origin", "frame": 0, "U2": 0.0, "RF2": 0.0})

    # Identify RP node label if available
    rp_label = None
    for assembly_nset_name, nset in odb.rootAssembly.nodeSets.items():
        if assembly_nset_name.upper().endswith("RP") or assembly_nset_name.upper() == "RP":
            nodes = nset.nodes
            if nodes:
                # nodes may be a list of Node objects across instances
                first = nodes[0]
                if hasattr(first, "label"):
                    rp_label = first.label
                elif isinstance(first, (list, tuple)) and first:
                    rp_label = first[0].label
            break

    continuous_u2 = 0.0
    prev_u2 = None
    peak_rf2 = None
    peak_u2 = None
    for step_name in step_names:
        step = odb.steps[step_name]
        for frame in step.frames:
            # Prefer history? Use field at RP
            u_field = frame.fieldOutputs["U"]
            rf_field = frame.fieldOutputs["RF"] if "RF" in frame.fieldOutputs.keys() else None
            u2 = None
            rf2 = None
            # Try assembly set RP
            try:
                if "RP" in odb.rootAssembly.nodeSets:
                    u_sub = u_field.getSubset(region=odb.rootAssembly.nodeSets["RP"])
                    if u_sub.values:
                        u2 = float(u_sub.values[0].data[1])
                    if rf_field is not None:
                        rf_sub = rf_field.getSubset(region=odb.rootAssembly.nodeSets["RP"])
                        if rf_sub.values:
                            rf2 = float(rf_sub.values[0].data[1])
            except Exception:
                pass
            if u2 is None and rp_label is not None:
                for val in u_field.values:
                    if val.nodeLabel == rp_label:
                        u2 = float(val.data[1])
                        break
            if rf2 is None and rf_field is not None and rp_label is not None:
                for val in rf_field.values:
                    if val.nodeLabel == rp_label:
                        rf2 = float(val.data[1])
                        break
            if u2 is None:
                continue
            if rf2 is None:
                rf2 = 0.0
            # step-aware continuous displacement: use reported U2 which is total prescribed in this model
            continuous_u2 = u2
            rows.append(
                {
                    "step": step_name,
                    "frame": frame.frameId,
                    "U2": continuous_u2,
                    "RF2": rf2,
                }
            )
            if peak_rf2 is None or rf2 > peak_rf2:
                peak_rf2 = rf2
                peak_u2 = continuous_u2

    # Write XY report and CSV
    rpt_path = os.path.join(outdir, f"{case_id}_RF2_U2.rpt")
    csv_path = os.path.join(outdir, f"{case_id}_RF2_U2.csv")
    with open(rpt_path, "w") as fh:
        fh.write("X Y\n")
        fh.write("U2 RF2\n")
        for row in rows:
            fh.write("{:.10g} {:.10g}\n".format(row["U2"], row["RF2"]))
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["step", "frame", "U2", "RF2"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Initial tangent stiffness from first positive-displacement point after origin
    k0 = None
    for row in rows[1:]:
        if abs(row["U2"]) > 1.0e-12:
            k0 = row["RF2"] / row["U2"]
            break

    summary = {
        "case_id": case_id,
        "odb": odb_path,
        "n_points": len(rows),
        "peak_RF2": peak_rf2,
        "U2_at_peak": peak_u2,
        "final_RF2": rows[-1]["RF2"] if rows else None,
        "final_U2": rows[-1]["U2"] if rows else None,
        "initial_tangent_stiffness": k0,
        "origin_included": True,
        "variable_selection": {
            "displacement": "RP U2",
            "reaction": "RP RF2",
            "phase_contour": "SDV15 on umatelem if available",
        },
    }
    with open(os.path.join(outdir, f"{case_id}_postprocess_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    # Viewport images: final SDV15 if present
    try:
        vp = session.viewports["Viewport: 1"]
        vp.setValues(displayedObject=odb)
        # Prefer last frame
        last_step = odb.steps[step_names[-1]]
        last_frame = last_step.frames[-1]
        vp.odbDisplay.setFrame(step=step_names[-1], frame=last_frame.frameId)
        keys = list(last_frame.fieldOutputs.keys())
        sdv_key = None
        for candidate in ("SDV15", "SDV"):
            if candidate in keys:
                sdv_key = candidate
                break
        if sdv_key is not None:
            vp.odbDisplay.setPrimaryVariable(
                variableLabel=sdv_key,
                outputPosition=last_frame.fieldOutputs[sdv_key].location,
            )
        session.printOptions.setValues(vpDecorations=OFF, reduceColors=False)
        session.printToFile(
            fileName=os.path.join(outdir, f"{case_id}_final_sdv_contour"),
            format=PNG,
            canvasObjects=(vp,),
        )
        session.printToFile(
            fileName=os.path.join(outdir, f"{case_id}_final_crack_path"),
            format=PNG,
            canvasObjects=(vp,),
        )
        session.printToFile(
            fileName=os.path.join(outdir, f"{case_id}_mesh_image"),
            format=PNG,
            canvasObjects=(vp,),
        )
    except Exception as exc:
        with open(os.path.join(outdir, f"{case_id}_image_export_warning.txt"), "w") as fh:
            fh.write(str(exc))

    # Command record
    with open(os.path.join(outdir, f"{case_id}_cae_commands.txt"), "w") as fh:
        fh.write("abaqus cae noGUI=postprocess_molnar_h_convergence_case.py -- ")
        fh.write("{} {} {}\n".format(odb_path, outdir, case_id))
        fh.write("variable_selection: RP U2, RP RF2, SDV15/SDV contour\n")
        fh.write("origin_point: forced (0,0)\n")

    with open(os.path.join(outdir, f"{case_id}_postprocess_manifest.json"), "w") as fh:
        json.dump(
            {
                "case_id": case_id,
                "outputs": [
                    os.path.basename(rpt_path),
                    os.path.basename(csv_path),
                    f"{case_id}_postprocess_summary.json",
                    f"{case_id}_cae_commands.txt",
                ],
                "summary": summary,
            },
            fh,
            indent=2,
            sort_keys=True,
        )

    odb.close()


if __name__ == "__main__":
    main()
