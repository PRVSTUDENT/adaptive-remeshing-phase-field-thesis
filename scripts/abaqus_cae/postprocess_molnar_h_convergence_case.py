# Abaqus/CAE noGUI postprocessing for one Molnar lc015 h-convergence case.
# Run with: abaqus cae noGUI=postprocess_molnar_h_convergence_case.py -- <odb> <outdir> <case_id>
#
# Compatibility: written for the installed Abaqus Python interpreter
# (no f-strings, no type annotations, no pathlib).
# Do not run with system Python for ODB access.

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
        args = []
        for a in sys.argv[1:]:
            if not a.endswith(".py"):
                args.append(a)
    if len(args) < 3:
        raise RuntimeError(
            "Usage: abaqus cae noGUI=script.py -- <odb> <outdir> <case_id>"
        )
    return args[0], args[1], args[2]


def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def _field_has_key(field_outputs, key):
    try:
        keys = field_outputs.keys()
    except Exception:
        try:
            keys = list(field_outputs.keys())
        except Exception:
            return False
    return key in keys


def main():
    odb_path, outdir, case_id = _args()
    _ensure_dir(outdir)

    from abaqus import session
    from abaqusConstants import OFF, PNG
    from odbAccess import openOdb

    odb = openOdb(path=odb_path, readOnly=True)
    step_names = list(odb.steps.keys())
    rows = []
    # Explicit origin
    rows.append({"step": "origin", "frame": 0, "U2": 0.0, "RF2": 0.0})

    rp_label = None
    try:
        nset_items = odb.rootAssembly.nodeSets.items()
    except Exception:
        nset_items = []
    for assembly_nset_name, nset in nset_items:
        name_up = str(assembly_nset_name).upper()
        if name_up.endswith("RP") or name_up == "RP":
            nodes = nset.nodes
            if nodes:
                first = nodes[0]
                if hasattr(first, "label"):
                    rp_label = first.label
                elif isinstance(first, (list, tuple)) and first:
                    rp_label = first[0].label
            break

    peak_rf2 = None
    peak_u2 = None
    for step_name in step_names:
        step = odb.steps[step_name]
        for frame in step.frames:
            u_field = frame.fieldOutputs["U"]
            rf_field = None
            if _field_has_key(frame.fieldOutputs, "RF"):
                rf_field = frame.fieldOutputs["RF"]
            u2 = None
            rf2 = None
            try:
                if "RP" in odb.rootAssembly.nodeSets:
                    u_sub = u_field.getSubset(region=odb.rootAssembly.nodeSets["RP"])
                    if u_sub.values:
                        u2 = float(u_sub.values[0].data[1])
                    if rf_field is not None:
                        rf_sub = rf_field.getSubset(
                            region=odb.rootAssembly.nodeSets["RP"]
                        )
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

    rpt_path = os.path.join(outdir, "{0}_RF2_U2.rpt".format(case_id))
    csv_path = os.path.join(outdir, "{0}_RF2_U2.csv".format(case_id))
    fh = open(rpt_path, "w")
    try:
        fh.write("X Y\n")
        fh.write("U2 RF2\n")
        for row in rows:
            fh.write("{0:.10g} {1:.10g}\n".format(row["U2"], row["RF2"]))
    finally:
        fh.close()

    # Binary mode for csv module compatibility across Abaqus Python versions
    try:
        fh = open(csv_path, "wb")
        binary_csv = True
    except Exception:
        fh = open(csv_path, "w")
        binary_csv = False
    try:
        writer = csv.DictWriter(fh, fieldnames=["step", "frame", "U2", "RF2"])
        if hasattr(writer, "writeheader"):
            writer.writeheader()
        else:
            writer.writerow(
                {"step": "step", "frame": "frame", "U2": "U2", "RF2": "RF2"}
            )
        for row in rows:
            if binary_csv:
                writer.writerow(
                    {
                        "step": str(row["step"]),
                        "frame": str(row["frame"]),
                        "U2": str(row["U2"]),
                        "RF2": str(row["RF2"]),
                    }
                )
            else:
                writer.writerow(row)
    finally:
        fh.close()

    k0 = None
    for row in rows[1:]:
        if abs(row["U2"]) > 1.0e-12:
            k0 = row["RF2"] / row["U2"]
            break

    final_rf2 = None
    final_u2 = None
    if rows:
        final_rf2 = rows[-1]["RF2"]
        final_u2 = rows[-1]["U2"]

    summary = {
        "case_id": case_id,
        "odb": odb_path,
        "n_points": len(rows),
        "peak_RF2": peak_rf2,
        "U2_at_peak": peak_u2,
        "final_RF2": final_rf2,
        "final_U2": final_u2,
        "initial_tangent_stiffness": k0,
        "origin_included": True,
        "variable_selection": {
            "displacement": "RP U2",
            "reaction": "RP RF2",
            "phase_contour": "SDV15 on umatelem if available",
        },
    }
    summary_path = os.path.join(
        outdir, "{0}_postprocess_summary.json".format(case_id)
    )
    fh = open(summary_path, "w")
    try:
        json.dump(summary, fh, indent=2, sort_keys=True)
    finally:
        fh.close()

    # Viewport images: final SDV if present
    try:
        vp = session.viewports["Viewport: 1"]
        vp.setValues(displayedObject=odb)
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
            fileName=os.path.join(outdir, "{0}_final_sdv_contour".format(case_id)),
            format=PNG,
            canvasObjects=(vp,),
        )
        session.printToFile(
            fileName=os.path.join(outdir, "{0}_final_crack_path".format(case_id)),
            format=PNG,
            canvasObjects=(vp,),
        )
        session.printToFile(
            fileName=os.path.join(outdir, "{0}_mesh_image".format(case_id)),
            format=PNG,
            canvasObjects=(vp,),
        )
    except Exception:
        warn_path = os.path.join(
            outdir, "{0}_image_export_warning.txt".format(case_id)
        )
        fh = open(warn_path, "w")
        try:
            fh.write(str(sys.exc_info()[1]))
        finally:
            fh.close()

    cmd_path = os.path.join(outdir, "{0}_cae_commands.txt".format(case_id))
    fh = open(cmd_path, "w")
    try:
        fh.write(
            "abaqus cae noGUI=postprocess_molnar_h_convergence_case.py -- "
        )
        fh.write("{0} {1} {2}\n".format(odb_path, outdir, case_id))
        fh.write("variable_selection: RP U2, RP RF2, SDV15/SDV contour\n")
        fh.write("origin_point: forced (0,0)\n")
    finally:
        fh.close()

    manifest_path = os.path.join(
        outdir, "{0}_postprocess_manifest.json".format(case_id)
    )
    fh = open(manifest_path, "w")
    try:
        json.dump(
            {
                "case_id": case_id,
                "outputs": [
                    os.path.basename(rpt_path),
                    os.path.basename(csv_path),
                    "{0}_postprocess_summary.json".format(case_id),
                    "{0}_cae_commands.txt".format(case_id),
                ],
                "summary": summary,
            },
            fh,
            indent=2,
            sort_keys=True,
        )
    finally:
        fh.close()

    odb.close()


if __name__ == "__main__":
    main()
