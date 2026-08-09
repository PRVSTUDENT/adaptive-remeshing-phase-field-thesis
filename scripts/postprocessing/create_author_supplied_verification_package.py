#!/usr/bin/env python3
"""Create the approved verification ZIP and supervisor PDF."""


import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
RUN = ROOT / "runs" / "molnar_single_notch_author_supplied_exact" / "20260720_abaqus_cae_reproduction"
FIG = RUN / "figure_review_v1"
REPORT = RUN / "report"
STAGING = REPORT / "verification_package_staging" / "Molnar_Author_SingleNotch_Verification_Package_20260720"
ZIP = REPORT / "Molnar_Author_SingleNotch_Verification_Package_20260720.zip"
PDF = REPORT / "Molnar_Author_SingleNotch_Supervisor_Report_Revised.pdf"
PDF_RENDER_DIR = ROOT / "tmp" / "pdfs" / "author_supplied_supervisor_report_render"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dest: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def reset_staging() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)
    if ZIP.exists():
        ZIP.unlink()


def stage_files() -> list[tuple[str, Path]]:
    items = [
        ("01_Original_Author_Files/SingleNotch.inp", RUN / "input" / "SingleNotch.inp"),
        ("01_Original_Author_Files/SingleNotch.for", RUN / "input" / "SingleNotch.for"),
        ("01_Original_Author_Files/AUTHOR_SUPPLIED_INPUT_PROVENANCE.md", RUN / "AUTHOR_SUPPLIED_INPUT_PROVENANCE.md"),
        ("02_Abaqus_CAE_Evidence/cae_author_supplied_rf2_u2.rpt", RUN / "cae_exports" / "cae_author_supplied_rf2_u2.rpt"),
        ("02_Abaqus_CAE_Evidence/cae_author_supplied_vs_fig7_lc_0p015.png", RUN / "cae_exports" / "cae_author_supplied_vs_fig7_lc_0p015.png"),
        ("02_Abaqus_CAE_Evidence/cae_model_geometry_mesh.png", RUN / "cae_exports" / "cae_model_geometry_mesh.png"),
        ("02_Abaqus_CAE_Evidence/cae_final_sdv15_contour.png", RUN / "cae_exports" / "cae_final_sdv15_contour.png"),
        ("02_Abaqus_CAE_Evidence/cae_final_sdv16_contour.png", RUN / "cae_exports" / "cae_final_sdv16_contour.png"),
        ("02_Abaqus_CAE_Evidence/export_author_supplied_cae_package.py", ROOT / "scripts" / "postprocessing" / "export_author_supplied_cae_package.py"),
        ("02_Abaqus_CAE_Evidence/CAE_COMPATIBILITY_NOTE.md", FIG / "notes" / "CAE_COMPATIBILITY_NOTE.md"),
        ("03_Clean_Report_Figures/geometry_mesh_clean.png", FIG / "contours" / "geometry_mesh_clean.png"),
        ("03_Clean_Report_Figures/author_supplied_vs_fig7_lc_0p015_clean.png", FIG / "plots" / "author_supplied_vs_fig7_lc_0p015_clean.png"),
        ("03_Clean_Report_Figures/author_supplied_vs_fig7_lc_0p015_clean.pdf", FIG / "plots" / "author_supplied_vs_fig7_lc_0p015_clean.pdf"),
        ("03_Clean_Report_Figures/author_supplied_vs_fig7_lc_0p015_clean_minimal.png", FIG / "plots" / "author_supplied_vs_fig7_lc_0p015_clean_minimal.png"),
        ("03_Clean_Report_Figures/sdv15_final_clean.png", FIG / "contours" / "sdv15_final_clean.png"),
        ("03_Clean_Report_Figures/sdv16_final_linear_clean.png", FIG / "contours" / "sdv16_final_linear_clean.png"),
        ("03_Clean_Report_Figures/author_supplied_reproduction_summary_panel.png", FIG / "panels" / "author_supplied_reproduction_summary_panel.png"),
        ("04_Data/cae_author_supplied_rf2_u2.csv", RUN / "cae_exports" / "cae_author_supplied_rf2_u2.csv"),
        ("04_Data/FIG7_LC_0P015_DIGITIZATION.md", RUN / "digitization" / "FIG7_LC_0P015_DIGITIZATION.md"),
        ("04_Data/fig7_lc_0p015_digitization_overlay.png", RUN / "digitization" / "fig7_lc_0p015_digitization_overlay.png"),
        ("04_Data/fig7_lc_0p015_raw.csv", RUN / "digitization" / "fig7_lc_0p015_raw.csv"),
        ("04_Data/fig7_lc_0p015_processed.csv", RUN / "digitization" / "fig7_lc_0p015_processed.csv"),
        ("04_Data/comparison_metrics.json", RUN / "report" / "comparison_metrics.json"),
        ("05_Reports/AUTHOR_SUPPLIED_SINGLE_NOTCH_CAE_REPRODUCTION.md", RUN / "AUTHOR_SUPPLIED_SINGLE_NOTCH_CAE_REPRODUCTION.md"),
        ("05_Reports/AUTHOR_SUPPLIED_VS_PUBLICATION_MODEL_TABLE.md", RUN / "AUTHOR_SUPPLIED_VS_PUBLICATION_MODEL_TABLE.md"),
        ("05_Reports/FIGURE_CAPTIONS.md", FIG / "notes" / "FIGURE_CAPTIONS.md"),
        ("05_Reports/FIGURE_PROVENANCE.md", FIG / "notes" / "FIGURE_PROVENANCE.md"),
        ("06_Run_Completion_Evidence/Molnar_Author_SingleNotch_Exact.sta", RUN / "evidence" / "Molnar_Author_SingleNotch_Exact.sta"),
        ("06_Run_Completion_Evidence/return_code.txt", RUN / "evidence" / "return_code.txt"),
        ("06_Run_Completion_Evidence/work_file_sha256.txt", RUN / "evidence" / "work_file_sha256.txt"),
        ("06_Run_Completion_Evidence/terminal_output.txt", RUN / "evidence" / "terminal_output.txt"),
    ]
    staged: list[tuple[str, Path]] = []
    for rel, src in items:
        dest = STAGING / rel
        copy_file(src, dest)
        staged.append((rel, dest))
    return staged


def write_index(staged: list[tuple[str, Path]]) -> None:
    lines = [
        "# Molnar Author-Supplied SingleNotch Verification Package",
        "",
        "Date: 2026-07-20",
        "",
        "This package verifies the exact author-supplied supplementary Molnar and Gravouil single-notch reproduction and the supervisor-facing presentation figures.",
        "",
        "Not included: ODB files, SIM files, compiled user-subroutine libraries, temporary Abaqus files, raw LaTeX build files, candidate-v2 files, Stage B planning files, or the power-normalized SDV16 figure as a primary result.",
        "",
        "The revised supervisor PDF is delivered separately as:",
        "",
        "`Molnar_Author_SingleNotch_Supervisor_Report_Revised.pdf`",
        "",
        "## File Index",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    for rel, path in staged:
        lines.append(f"| `{rel}` | {path.stat().st_size} | `{sha256(path)}` |")
    lines.extend(
        [
            "",
            "## Recommended Primary Report Figures",
            "",
            "- `03_Clean_Report_Figures/geometry_mesh_clean.png`",
            "- `03_Clean_Report_Figures/author_supplied_vs_fig7_lc_0p015_clean.png`",
            "- `03_Clean_Report_Figures/sdv15_final_clean.png`",
            "- `03_Clean_Report_Figures/sdv16_final_linear_clean.png`",
            "",
            "## Verification Highlights",
            "",
            "- Digitization audit files are in `04_Data/`.",
            "- Lightweight run-completion evidence is in `06_Run_Completion_Evidence/`.",
            "- The revised supervisor PDF should be sent alongside this ZIP.",
        ]
    )
    index = STAGING / "01_README_AND_FILE_INDEX.md"
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_metrics() -> dict:
    return json.loads((RUN / "report" / "comparison_metrics.json").read_text())


def count_csv_rows(path: Path) -> int:
    with path.open(newline="") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def scaled_image(path: Path, width_cm: float, max_height_cm: float | None = None) -> RLImage:
    im = Image.open(path)
    width = width_cm * cm
    height = width * im.height / im.width
    if max_height_cm is not None and height > max_height_cm * cm:
        height = max_height_cm * cm
        width = height * im.width / im.height
    return RLImage(str(path), width=width, height=height)


def make_supervisor_pdf() -> None:
    metrics = read_metrics()
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15, spaceBefore=8, spaceAfter=5)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12, spaceAfter=5)
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=10)

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.25 * cm,
        bottomMargin=1.25 * cm,
    )
    story = []
    story.append(Paragraph("Author-Supplied Molnar Single-Notch Reproduction", title))
    story.append(Paragraph("Supervisor review summary - exact supplementary model", body))
    story.append(Paragraph("Scope and Provenance", h2))
    story.append(
        Paragraph(
            "The original author-supplied SingleNotch input deck and Fortran user subroutine were copied byte-identically and run locally in Abaqus 2024 with cpus=1. "
            "The source hashes match the preserved originals. The run completed successfully and the ODB was readable. The clean figures below are presentation restyling from Abaqus/CAE-exported data; no scientific values were modified.",
            body,
        )
    )
    summary_data = [
        ["Item", "Result"],
        ["Technical execution", "Successfully completed"],
        ["Scientific comparison", "No one-to-one match with digitized Fig. 7"],
        ["Simulation peak", f"{metrics['simulation_peak']['rf2_kN']:.6f} kN at U2 = {metrics['simulation_peak']['u2_mm']:.6f} mm"],
        ["Digitized Fig. 7 peak", f"{metrics['reference_peak']['force_kN']:.6f} kN at u = {metrics['reference_peak']['u_mm']:.6f} mm"],
        ["Peak force error", f"{metrics['peak_force_error_relative_to_reference'] * 100:.2f}%"],
        ["Peak displacement error", f"{metrics['peak_displacement_error_relative_to_reference'] * 100:.2f}%"],
        ["Full-curve NRMSE", f"{metrics['full_curve_nrmse']:.4f} ({metrics['full_curve_nrmse'] * 100:.2f}%)"],
    ]
    table = Table(summary_data, colWidths=[5.1 * cm, 11.3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9aa0a6")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.18 * cm))
    story.append(scaled_image(FIG / "contours" / "geometry_mesh_clean.png", 12.2, 10.4))
    story.append(Paragraph("Figure 1. Author-supplied single-notch mesh and exact boundary-condition interpretation from the input deck.", small))
    story.append(PageBreak())

    story.append(Paragraph("RF2-U2 Comparison", h2))
    story.append(scaled_image(FIG / "plots" / "author_supplied_vs_fig7_lc_0p015_clean.png", 16.8, 12.2))
    story.append(
        Paragraph(
            "Figure 2. RF2-U2 comparison for the exact author-supplied supplementary model and digitized Molnar Fig. 7 points for lc = 0.015 mm. "
            "Both curves begin at the origin. The digitized curve is approximate publication-image data, not exact author numerical data.",
            small,
        )
    )
    story.append(Paragraph("Crack Path and History-State Evidence", h2))
    story.append(scaled_image(FIG / "contours" / "sdv15_final_clean.png", 15.2, 9.1))
    story.append(
        Paragraph(
            "Figure 3. Final SDV15 field. The presentation field is reconstructed as the element-wise mean of Abaqus-exported integration-point SDV15 values; the underlying numerical values were not modified.",
            small,
        )
    )
    story.append(PageBreak())
    story.append(Paragraph("Final SDV16 Linear-Scale Result", h2))
    story.append(scaled_image(FIG / "contours" / "sdv16_final_linear_clean.png", 15.2, 11.0))
    story.append(Paragraph("Figure 4. Final SDV16 history/driving-state field using a linear color scale. This is the primary SDV16 figure for scientific reporting.", small))
    story.append(Paragraph("Supplement Versus Publication-Scale Model", h2))
    story.append(
        Paragraph(
            "The supplement is exact as supplied, but it is not automatically identical to the publication-scale model. The supplied model uses lc = 0.015 mm, 3930 physical elements, and local h = 0.005 mm. The publication-scale description reports approximately 22000 physical elements and h = 0.001 mm near the crack path. These documented differences may contribute to the RF-U mismatch, but their individual effects have not yet been isolated through a controlled study.",
            body,
        )
    )
    story.append(
        Paragraph(
            f"Validation data: RF-U simulation CSV rows = {count_csv_rows(RUN / 'cae_exports' / 'cae_author_supplied_rf2_u2.csv')}; digitized Fig. 7 processed rows = {count_csv_rows(RUN / 'digitization' / 'fig7_lc_0p015_processed.csv')}. Direct Abaqus/CAE evidence is retained in the verification ZIP.",
            small,
        )
    )
    story.append(Paragraph("Requested Guidance", h2))
    story.append(
        Paragraph(
            "The exact supplied supplementary model does not reproduce the digitized Figure 7 curve one-to-one. I would appreciate guidance on whether the next step should be:",
            body,
        )
    )
    guidance_data = [
        ["1.", "reconstruction of the finer publication-scale model;"],
        ["2.", "a controlled mesh-sensitivity study beginning from the supplied model; or"],
        ["3.", "contacting the authors for the exact Figure 7 model and numerical data."],
    ]
    guidance = Table(guidance_data, colWidths=[0.7 * cm, 15.6 * cm])
    guidance.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )
    story.append(guidance)
    doc.build(story)


def render_pdf() -> list[Path]:
    if PDF_RENDER_DIR.exists():
        shutil.rmtree(PDF_RENDER_DIR)
    PDF_RENDER_DIR.mkdir(parents=True)
    prefix = PDF_RENDER_DIR / "page"
    subprocess.run(["pdftoppm", "-png", "-r", "150", str(PDF), str(prefix)], check=True)
    return sorted(PDF_RENDER_DIR.glob("page-*.png"))


def make_zip() -> None:
    shutil.make_archive(str(ZIP.with_suffix("")), "zip", root_dir=STAGING.parent, base_dir=STAGING.name)


def validate_package() -> None:
    forbidden_suffixes = {".odb", ".sim", ".dll", ".obj", ".lib", ".exp", ".lck"}
    forbidden_names = {"Molnar_Author_SingleNotch_Exact.odb"}
    for path in STAGING.rglob("*"):
        if path.is_file():
            if path.suffix.lower() in forbidden_suffixes or path.name in forbidden_names:
                raise RuntimeError(f"forbidden file staged: {path}")
            if "paper_matched_single_notch_v2" in str(path).lower() or "stage_b" in str(path).lower():
                raise RuntimeError(f"forbidden candidate/stage file staged: {path}")
    if not ZIP.exists() or ZIP.stat().st_size == 0:
        raise RuntimeError("ZIP was not created")
    if not PDF.exists() or PDF.stat().st_size == 0:
        raise RuntimeError("PDF was not created")


def main() -> int:
    reset_staging()
    staged = stage_files()
    write_index(staged)
    make_supervisor_pdf()
    rendered = render_pdf()
    if not rendered:
        raise RuntimeError("PDF render produced no pages")
    make_zip()
    validate_package()
    print(f"ZIP: {ZIP}")
    print(f"PDF: {PDF}")
    print("Rendered PDF pages:")
    for path in rendered:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
