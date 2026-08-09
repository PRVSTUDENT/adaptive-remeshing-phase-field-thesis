"""Export Abaqus/CAE figures and XY data for the author-supplied SingleNotch run.

Run with:
    abaqus cae noGUI=scripts/postprocessing/export_author_supplied_cae_package.py
"""

from __future__ import print_function

import csv
import json
import os
import sys

from abaqus import session  # type: ignore
from visualization import openOdb as openVisualizationOdb  # type: ignore
from abaqusConstants import (  # type: ignore
    CONTOURS_ON_DEF,
    DEFORMED,
    ALL,
    INTEGRATION_POINT,
    OFF,
    ON,
    PNG,
    UNDEFORMED,
)
from odbAccess import openOdb  # type: ignore


ROOT = r"D:\Master thesis\Adaptive remeshing"
RUN_DIR = os.path.join(
    ROOT,
    "runs",
    "molnar_single_notch_author_supplied_exact",
    "20260720_abaqus_cae_reproduction",
)
ODB_PATH = os.path.join(RUN_DIR, "work", "Molnar_Author_SingleNotch_Exact.odb")
REF_PATH = os.path.join(RUN_DIR, "digitization", "fig7_lc_0p015_processed.csv")
OUT_DIR = os.path.join(RUN_DIR, "cae_exports")
JOB = "Molnar_Author_SingleNotch_Exact"


def value_component(value, component_index):
    data = value.data
    try:
        return float(data[component_index])
    except (TypeError, IndexError):
        return float(data)


def scalar_value(value):
    data = value.data
    try:
        return float(data[0])
    except (TypeError, IndexError):
        return float(data)


def get_single_subset_value(field, region):
    subset = field.getSubset(region=region)
    if not subset.values:
        return None
    return subset.values[0]


def extract_curve_and_matches(odb_path):
    odb = openOdb(path=odb_path, readOnly=True)
    try:
        rp = odb.rootAssembly.nodeSets["RP"]
        rows = []
        elapsed = 0.0
        previous_step_duration = 0.0
        last_u = None
        last_rf = None
        for step_index, (step_name, step) in enumerate(odb.steps.items()):
            if step_index > 0:
                elapsed = previous_step_duration
            for frame_index, frame in enumerate(step.frames):
                u = ""
                rf = ""
                if "U" in frame.fieldOutputs:
                    value = get_single_subset_value(frame.fieldOutputs["U"], rp)
                    if value is not None:
                        u = value_component(value, 1)
                if "RF" in frame.fieldOutputs:
                    value = get_single_subset_value(frame.fieldOutputs["RF"], rp)
                    if value is not None:
                        rf = value_component(value, 1)
                if u == "" or rf == "":
                    continue
                if (
                    rows
                    and abs(float(u) - float(last_u)) < 1.0e-12
                    and abs(float(rf) - float(last_rf)) < 1.0e-12
                ):
                    continue
                rows.append(
                    {
                        "step": step_name,
                        "frame": frame_index,
                        "step_time": float(frame.frameValue),
                        "analysis_time": elapsed + float(frame.frameValue),
                        "u2_mm": float(u),
                        "rf2_kN": float(rf),
                    }
                )
                last_u = u
                last_rf = rf
            previous_step_duration += float(step.frames[-1].frameValue)

        if rows and (abs(rows[0]["u2_mm"]) > 1.0e-14 or abs(rows[0]["rf2_kN"]) > 1.0e-14):
            rows.insert(
                0,
                {
                    "step": "origin",
                    "frame": 0,
                    "step_time": 0.0,
                    "analysis_time": 0.0,
                    "u2_mm": 0.0,
                    "rf2_kN": 0.0,
                },
            )

        targets = [0.002, 0.005, 0.006, rows[-1]["u2_mm"]]
        matches = []
        for target in targets:
            match = min(rows, key=lambda row: abs(abs(row["u2_mm"]) - abs(target)))
            matches.append(dict(match, target_u2_mm=target, abs_u2_error=abs(abs(match["u2_mm"]) - abs(target))))

        final_frame = {
            "step": list(odb.steps.keys())[-1],
            "frame": len(list(odb.steps.values())[-1].frames) - 1,
        }
        return rows, matches, final_frame
    finally:
        odb.close()


def read_reference(path):
    rows = []
    with open(path, "r") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            rows.append((float(row["u_mm"]), float(row["reaction_force_kN"])))
    return rows


def write_rpt(path, simulation_rows, reference_rows):
    with open(path, "w") as stream:
        stream.write("Abaqus/CAE XY Report\n")
        stream.write("Job: %s\n" % JOB)
        stream.write("Simulation: assembly node set RP, RF2 versus U2, both steps, duplicate consecutive frames removed\n")
        stream.write("Reference: digitized Molnar Fig. 7 black solid lc=0.015 mm curve\n")
        stream.write("Sign convention: ODB RF2 is reported directly; positive plotted force is positive RF2 at RP\n")
        stream.write("\n")
        stream.write("simulation_u2_mm,simulation_rf2_kN\n")
        for row in simulation_rows:
            stream.write("%.12g,%.12g\n" % (row["u2_mm"], row["rf2_kN"]))
        stream.write("\n")
        stream.write("reference_u_mm,reference_force_kN\n")
        for u, force in reference_rows:
            stream.write("%.12g,%.12g\n" % (u, force))


def write_curve_csv(path, rows):
    with open(path, "w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["step", "frame", "step_time", "analysis_time", "u2_mm", "rf2_kN"],
        )
        writer.writeheader()
        writer.writerows(rows)


def make_xy_plot(simulation_rows, reference_rows):
    sim_data = tuple((row["u2_mm"], row["rf2_kN"]) for row in simulation_rows)
    ref_data = tuple(reference_rows)
    peak_sim = max(simulation_rows, key=lambda row: row["rf2_kN"])
    peak_ref_u, peak_ref_f = max(reference_rows, key=lambda item: item[1])

    sim_xy = session.XYData(name="author_supplied_RF2_vs_U2_RP", data=sim_data)
    ref_xy = session.XYData(name="fig7_lc_0p015_digitized", data=ref_data)
    origin_xy = session.XYData(name="origin", data=((0.0, 0.0),))
    peaks_xy = session.XYData(
        name="peak_points",
        data=((peak_sim["u2_mm"], peak_sim["rf2_kN"]), (peak_ref_u, peak_ref_f)),
    )
    plot = session.XYPlot(name="author_supplied_vs_fig7_lc_0p015")
    chart_name = list(plot.charts.keys())[0]
    chart = plot.charts[chart_name]
    curves = (
        session.Curve(xyData=sim_xy),
        session.Curve(xyData=ref_xy),
        session.Curve(xyData=origin_xy),
        session.Curve(xyData=peaks_xy),
    )
    chart.setValues(curvesToPlot=curves)
    chart.axes1[0].axisData.setValues(title="U2 at RP [mm]")
    chart.axes2[0].axisData.setValues(title="RF2 at RP [kN]")
    vp = session.Viewport(name="CAE RF2-U2 comparison", origin=(0, 0), width=180, height=120)
    vp.setValues(displayedObject=plot)
    session.printToFile(
        fileName=os.path.join(OUT_DIR, "cae_author_supplied_vs_fig7_lc_0p015"),
        format=PNG,
        canvasObjects=(vp,),
    )


def make_viewport_exports(matches, final_frame):
    odb = openVisualizationOdb(path=ODB_PATH)
    vp = session.Viewport(name="CAE ODB contour exports", origin=(0, 0), width=180, height=120)
    vp.setValues(displayedObject=odb)
    vp.odbDisplay.commonOptions.setValues(visibleEdges=ALL)
    vp.odbDisplay.display.setValues(plotState=(UNDEFORMED,))
    session.printToFile(
        fileName=os.path.join(OUT_DIR, "cae_model_geometry_mesh"),
        format=PNG,
        canvasObjects=(vp,),
    )

    for match in matches:
        step_index = list(odb.steps.keys()).index(match["step"])
        vp.odbDisplay.setFrame(step=step_index, frame=int(match["frame"]))
        try:
            vp.odbDisplay.setPrimaryVariable(variableLabel="SDV15", outputPosition=INTEGRATION_POINT)
            vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF,))
            session.printToFile(
                fileName=os.path.join(
                    OUT_DIR,
                    "cae_sdv15_u2_%0.4f" % abs(float(match["target_u2_mm"])),
                ).replace(".", "p"),
                format=PNG,
                canvasObjects=(vp,),
            )
        except Exception as exc:
            print("WARNING: SDV15 export failed for %s frame %s: %s" % (match["step"], match["frame"], exc))

    step_index = list(odb.steps.keys()).index(final_frame["step"])
    vp.odbDisplay.setFrame(step=step_index, frame=int(final_frame["frame"]))
    for variable in ["SDV15", "SDV16"]:
        try:
            vp.odbDisplay.setPrimaryVariable(variableLabel=variable, outputPosition=INTEGRATION_POINT)
            vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF,))
            session.printToFile(
                fileName=os.path.join(OUT_DIR, "cae_final_%s_contour" % variable.lower()),
                format=PNG,
                canvasObjects=(vp,),
            )
        except Exception as exc:
            print("WARNING: %s final export failed: %s" % (variable, exc))
    odb.close()


def main():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    simulation_rows, matches, final_frame = extract_curve_and_matches(ODB_PATH)
    reference_rows = read_reference(REF_PATH)
    write_rpt(os.path.join(OUT_DIR, "cae_author_supplied_rf2_u2.rpt"), simulation_rows, reference_rows)
    write_curve_csv(os.path.join(OUT_DIR, "cae_author_supplied_rf2_u2.csv"), simulation_rows)
    with open(os.path.join(OUT_DIR, "cae_export_summary.json"), "w") as stream:
        json.dump(
            {
                "odb": ODB_PATH,
                "reference": REF_PATH,
                "simulation_rows": len(simulation_rows),
                "reference_rows": len(reference_rows),
                "origin_check": {
                    "simulation_first": [simulation_rows[0]["u2_mm"], simulation_rows[0]["rf2_kN"]],
                    "reference_first": list(reference_rows[0]),
                },
                "matched_frames": matches,
                "final_frame": final_frame,
            },
            stream,
            indent=2,
            sort_keys=True,
        )
        stream.write("\n")
    make_xy_plot(simulation_rows, reference_rows)
    make_viewport_exports(matches, final_frame)
    print("CAE exports written to %s" % OUT_DIR)


if __name__ == "__main__":
    main()
