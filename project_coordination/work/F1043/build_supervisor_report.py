from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
WORK = ROOT / "project_coordination" / "work" / "F1043"
FIG = WORK / "figures"
OUT = ROOT / "docs" / "supervisor_reports" / "17-09-2026" / "SUPERVISOR_MEETING_REPORT_MODE1_2026-09-17.docx"
FIG.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

BLUE = "17365D"
MID_BLUE = "2F75B5"
LIGHT_BLUE = "DDEBF7"
PALE_BLUE = "EEF5FB"
GRAY = "666666"
LIGHT_GRAY = "E7E6E6"
PALE_GRAY = "F7F7F7"
RED = "C00000"


def load_curve(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    names = {n.lower(): n for n in reader.fieldnames or []}
    u_name = names.get("u2_mm") or names.get("displacement_mm")
    f_name = names.get("rf2_kn") or names.get("reaction_force_kn")
    data = sorted((float(r[u_name]), float(r[f_name])) for r in rows)
    return [x for x, _ in data], [y for _, y in data]


def savefig(path: Path):
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def make_geometry():
    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, lw=2.2, color="#202020"))
    ax.plot([0, 0.5], [0.5, 0.5], color="#1F4E79", lw=4, solid_capstyle="butt")
    ax.scatter([0.5], [0.5], s=48, color="#C55A11", zorder=4)
    for x in (0.18, 0.5, 0.82):
        ax.annotate("", xy=(x, 1.18), xytext=(x, 1.01), arrowprops=dict(arrowstyle="->", lw=2.0, color="#202020"))
    ax.text(0.5, 1.22, "prescribed Mode-I opening displacement  $u_y$", ha="center", va="bottom", fontsize=12)
    for x in (0.12, 0.5, 0.88):
        ax.plot([x - 0.035, x + 0.035], [-0.045, -0.045], color="#202020", lw=1.4)
        ax.plot([x, x], [-0.045, 0], color="#202020", lw=1.4)
    ax.text(0.5, -0.15, "$u_y=0$ on the lower edge", ha="center", fontsize=11)
    ax.plot([0.0, 0.0], [0.0, -0.06], color="#C00000", lw=3)
    ax.annotate("$u_x=0$ point restraint", xy=(0.0, 0.0), xytext=(0.05, 0.21),
                arrowprops=dict(arrowstyle="->", lw=1.2, color="#C00000"),
                ha="left", va="center", color="#C00000", fontsize=9.5)
    ax.annotate("", xy=(1.08, 1), xytext=(1.08, 0), arrowprops=dict(arrowstyle="<->", lw=1.5))
    ax.text(1.11, 0.5, "1.0 mm", rotation=90, va="center", fontsize=11)
    ax.annotate("", xy=(1, -0.24), xytext=(0, -0.24), arrowprops=dict(arrowstyle="<->", lw=1.5))
    ax.text(0.5, -0.31, "1.0 mm", ha="center", fontsize=11)
    ax.text(0.13, 0.54, "zero-gap crack  $a_0=0.5$ mm", fontsize=11, color="#1F4E79")
    ax.text(0.52, 0.47, "crack tip", fontsize=10, color="#C55A11")
    ax.text(0.62, 0.08, "Publication: vertical loading and bottom support\nProject-only sensitivity: top-edge $U_1=0$", fontsize=8.5, color="#555555")
    ax.set_xlim(-0.12, 1.28)
    ax.set_ylim(-0.38, 1.34)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    savefig(FIG / "mode1_geometry.png")


def make_response_figures():
    curve_paths = {
        "Fixed reference 1398090": ROOT / "results" / "pandey_kumar_mode1" / "master_fracture_curves" / "curve_standard_1398090.csv",
        "Corrected nominal 1% 1404933": ROOT / "results" / "pandey_kumar_mode1" / "master_fracture_curves" / "curve_1404933_extracted.csv",
        "Defective preprocessing 1399632": ROOT / "results" / "pandey_kumar_mode1" / "master_fracture_curves" / "curve_adaptive_1399632.csv",
    }
    curves = {k: load_curve(v) for k, v in curve_paths.items()}
    colors = {"Fixed reference 1398090": "#202020", "Corrected nominal 1% 1404933": "#2F75B5", "Defective preprocessing 1399632": "#C00000"}
    styles = {"Fixed reference 1398090": "-", "Corrected nominal 1% 1404933": "-", "Defective preprocessing 1399632": "--"}

    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    for label, (u, f) in curves.items():
        ax.plot(u, f, label=label, color=colors[label], ls=styles[label], lw=2.0)
    peaks = [(0.005857, 0.757778, "#202020", "Reference peak"), (0.005750, 0.745325, "#2F75B5", "Corrected peak"), (0.004150, 0.478203, "#C00000", "Defective peak")]
    for u, f, c, t in peaks:
        ax.scatter([u], [f], color=c, s=35, zorder=5)
        ax.annotate(t, (u, f), xytext=(5, 5), textcoords="offset points", fontsize=8.5, color=c)
    ax.axvspan(0, 0.001, color="#DDEBF7", alpha=0.65, label="Project OLS range")
    ax.set(xlabel="Prescribed displacement u [mm]", ylabel="Total reaction force F [kN]", xlim=(0, 0.0075), ylim=(0, 0.84))
    ax.grid(True, ls=":", alpha=0.45)
    ax.legend(loc="best", frameon=False, fontsize=8.5)
    fig.tight_layout()
    savefig(FIG / "force_displacement_full.png")

    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    for label, (u, f) in curves.items():
        pts = [(x, y) for x, y in zip(u, f) if 0 <= x <= 0.001]
        ax.plot([x for x, _ in pts], [y for _, y in pts], label=label, color=colors[label], ls=styles[label], lw=2.2)
    ax.text(0.00061, 0.107, "$K_0=137.945520$ kN/mm", color="#202020", fontsize=9)
    ax.text(0.00061, 0.090, "$K_0=137.820804$ kN/mm", color="#2F75B5", fontsize=9)
    ax.text(0.00061, 0.073, r"$K_0\approx122.38$ kN/mm", color="#C00000", fontsize=9)
    ax.set(xlabel="Prescribed displacement u [mm]", ylabel="Total reaction force F [kN]", xlim=(0, 0.001), ylim=(0, 0.145))
    ax.grid(True, ls=":", alpha=0.45)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5)
    fig.tight_layout()
    savefig(FIG / "force_displacement_zoom.png")


def make_convergence_figures():
    import generate_convergence_figures as gcf
    gcf.generate_figure_a()
    gcf.generate_figure_b()


def flow_boxes(ax, labels, y, x0=0.02, x1=0.98, height=0.32, fontsize=8.4):
    n = len(labels)
    gap = 0.014
    width = (x1 - x0 - gap * (n - 1)) / n
    for i, label in enumerate(labels):
        x = x0 + i * (width + gap)
        ax.add_patch(Rectangle((x, y), width, height, facecolor="#EEF5FB", edgecolor="#2F75B5", lw=1.2))
        ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=fontsize)
        if i < n - 1:
            ax.add_patch(FancyArrowPatch((x + width, y + height / 2), (x + width + gap, y + height / 2), arrowstyle="->", mutation_scale=11, lw=1.3, color="#555555"))


def make_workflow():
    fig, ax = plt.subplots(figsize=(11.0, 2.3))
    labels = ["Geometry + coarse\n$h=0.02$ mm", "Job-1.inp", "Python creates\nJob-1_UEL.inp", "Pre-analysis\nMISESERI on All_elem", "RemeshingRule", "adaptiveRemesh", "Job-2.inp", "Job-2_UEL.inp", "Final phase-field\nsolve"]
    flow_boxes(ax, labels, 0.33, fontsize=7.3)
    ax.text(0.5, 0.84, "Pandey-Kumar published two-job adaptive pre-refinement workflow", ha="center", fontsize=12.5, weight="bold", color="#17365D")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    savefig(FIG / "published_workflow.png")


def make_miseseri_concept():
    fig, ax = plt.subplots(figsize=(10.4, 2.1))
    ax.add_patch(Rectangle((0.03, 0.53), 0.26, 0.30, facecolor="#F2F2F2", edgecolor="#7F7F7F"))
    ax.text(0.16, 0.68, "lower MISESERI\nlower estimated stress error", ha="center", va="center", fontsize=10)
    ax.add_patch(FancyArrowPatch((0.30, 0.68), (0.47, 0.68), arrowstyle="->", mutation_scale=16, lw=1.5))
    ax.add_patch(Rectangle((0.48, 0.53), 0.27, 0.30, facecolor="#E2F0D9", edgecolor="#70AD47"))
    ax.text(0.615, 0.68, "little or no additional refinement", ha="center", va="center", fontsize=10)
    ax.add_patch(Rectangle((0.03, 0.08), 0.26, 0.30, facecolor="#FCE4D6", edgecolor="#C55A11"))
    ax.text(0.16, 0.23, "higher MISESERI\nlarger estimated stress error", ha="center", va="center", fontsize=10)
    ax.add_patch(FancyArrowPatch((0.30, 0.23), (0.47, 0.23), arrowstyle="->", mutation_scale=16, lw=1.5))
    ax.add_patch(Rectangle((0.48, 0.08), 0.20, 0.30, facecolor="#FFF2CC", edgecolor="#BF9000"))
    ax.text(0.58, 0.23, "smaller requested\nelement size", ha="center", va="center", fontsize=10)
    ax.add_patch(FancyArrowPatch((0.69, 0.23), (0.80, 0.23), arrowstyle="->", mutation_scale=16, lw=1.5))
    ax.add_patch(Rectangle((0.81, 0.08), 0.16, 0.30, facecolor="#DDEBF7", edgecolor="#2F75B5"))
    ax.text(0.89, 0.23, "more elements\nlocally", ha="center", va="center", fontsize=10)
    ax.text(0.89, 0.70, "Observed tendency under\nUNIFORM_ERROR sizing", ha="center", va="center", fontsize=9, color="#666666")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    savefig(FIG / "miseseri_concept.png")


def make_boundary_flow():
    fig, ax = plt.subplots(figsize=(10.5, 2.7))
    bad = ["Intended N_BOTTOM\n150 nodes", "single overlong\n*NSET data line", "Abaqus truncation\n16 retained", "134 nodes free\nvertically", "artificial lift and\nlow $K_0$"]
    good = ["wrap NSET\n<=16 entries per line", "150 / 150 nodes\nconstrained", "bottom lift\neliminated", "$K_0$ returns to\nreference level"]
    flow_boxes(ax, bad, 0.57, x0=0.02, x1=0.98, height=0.26, fontsize=8.6)
    flow_boxes(ax, good, 0.13, x0=0.15, x1=0.90, height=0.26, fontsize=8.8)
    ax.text(0.01, 0.70, "Defect", rotation=90, va="center", color="#C00000", weight="bold")
    ax.text(0.10, 0.26, "Repair", rotation=90, va="center", color="#548235", weight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    savefig(FIG / "boundary_set_flow.png")


def make_branch_diagram():
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.text(0.5, 0.95, "SAME MODE-I BENCHMARK", ha="center", va="center", fontsize=15, weight="bold", color="#17365D")
    ax.plot([0.18, 0.82], [0.89, 0.89], color="#7F7F7F", lw=1.6)
    for x in (0.18, 0.50, 0.82):
        ax.add_patch(FancyArrowPatch((x, 0.89), (x, 0.83), arrowstyle="->", mutation_scale=15, lw=1.4, color="#7F7F7F"))
    columns = [
        (0.03, 0.31, "PANDEY-KUMAR\nSTANDARD PFM", ["global $h=0.02$ mm", "manual crack-corridor refinement", "local $h=0.003$ mm", "26,282 elements"], "#F2F2F2", "#595959"),
        (0.35, 0.63, "PANDEY-KUMAR\nPROPOSED ADAPTIVE PFM", ["separate coarse model", "global $h=0.02$ mm", "no manual local refinement", "Job-1_UEL -> MISESERI", "adaptiveRemesh", "local $h=0.001$ mm", "13,941 elements", "initial count not reported"], "#E2F0D9", "#548235"),
        (0.67, 0.95, "PROJECT\nRECONSTRUCTION", ["coarse pre-analysis", "2,906 elements", "MISESERI", "errorTarget = 1.0", "adaptiveRemesh", "71,320 elements"], "#DDEBF7", "#2F75B5"),
    ]
    for x0, x1, title, lines, fc, ec in columns:
        ax.add_patch(Rectangle((x0, 0.23), x1-x0, 0.60, facecolor=fc, edgecolor=ec, lw=1.8))
        ax.text((x0+x1)/2, 0.77, title, ha="center", va="center", fontsize=10.5, weight="bold", color=ec)
        ys = [0.67 - i * (0.42 / max(1, len(lines)-1)) for i in range(len(lines))]
        for i, (line, y) in enumerate(zip(lines, ys)):
            weight = "bold" if ("elements" in line or "count not" in line) else "normal"
            ax.text((x0+x1)/2, y, line, ha="center", va="center", fontsize=9.1, weight=weight)
            if i < len(lines)-1:
                ax.add_patch(FancyArrowPatch(((x0+x1)/2, y-0.018), ((x0+x1)/2, ys[i+1]+0.020), arrowstyle="->", mutation_scale=10, lw=0.8, color=ec))
    ax.text(0.5, 0.13, "Do not read horizontally as 26,282 -> 13,941. The branches are independent discretization strategies.", ha="center", va="center", fontsize=11.2, weight="bold", color="#C00000")
    ax.text(0.5, 0.055, "Paper adaptive route: initial count not reported -> 13,941     |     Project adaptive route: 2,906 -> 71,320", ha="center", fontsize=10.3, color="#17365D")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    savefig(FIG / "three_branch_mesh_routes.png")


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell, color="D9D9D9", size="4"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        elem = borders.find(qn(tag))
        if elem is None:
            elem = OxmlElement(tag)
            borders.append(elem)
        elem.set(qn("w:val"), "single")
        elem.set(qn("w:sz"), size)
        elem.set(qn("w:color"), color)


def set_cell_margins(cell, top=75, start=90, bottom=75, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn("w:" + m))
        if node is None:
            node = OxmlElement("w:" + m)
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def font_run(run, size=9.3, bold=False, color="000000", italic=False):
    run.font.name = "Aptos"
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Aptos")
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def set_paragraph_font(paragraph, size=9.3, bold=False, color="000000", italic=False):
    for run in paragraph.runs:
        font_run(run, size=size, bold=bold, color=color, italic=italic)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    font_run(run, size=8.5, color=GRAY)
    fld_char1 = OxmlElement("w:fldChar"); fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar"); fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr, fld_char2])


def style_document(doc: Document):
    sec = doc.sections[0]
    sec.page_height = Cm(29.7); sec.page_width = Cm(21.0)
    sec.top_margin = Cm(1.55); sec.bottom_margin = Cm(1.45); sec.left_margin = Cm(1.65); sec.right_margin = Cm(1.65)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"; normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos"); normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(9.3); normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(4.2); normal.paragraph_format.line_spacing = 1.03
    for name, size in (("Title", 25), ("Heading 1", 16), ("Heading 2", 11.5)):
        s = styles[name]
        s.font.name = "Aptos Display"; s._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display"); s._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
        s.font.size = Pt(size); s.font.bold = True; s.font.color.rgb = RGBColor(0, 0, 0)
        s.paragraph_format.space_before = Pt(3); s.paragraph_format.space_after = Pt(6)
    header = sec.header.paragraphs[0]
    header.text = "Mode-I adaptive remeshing supervisor report"
    header.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_font(header, size=8.3, color=GRAY)
    add_page_number(sec.footer.paragraphs[0])


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def add_body(doc, text, bold_lead=None, size=9.3, space_after=4.2):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead); font_run(r, size=size, bold=True)
        r = p.add_run(text[len(bold_lead):]); font_run(r, size=size)
    else:
        r = p.add_run(text); font_run(r, size=size)
    return p


def add_bullets(doc, items, size=9.1):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Cm(0.55); p.paragraph_format.first_line_indent = Cm(-0.25)
        p.paragraph_format.space_after = Pt(2.3)
        r = p.add_run(item); font_run(r, size=size)


def add_caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text); font_run(r, size=8.0, italic=True, color=GRAY)
    return p


def add_source(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(3)
    r = p.add_run("Source: "); font_run(r, size=7.8, bold=True, color=GRAY)
    r = p.add_run(text); font_run(r, size=7.8, color=GRAY)


def add_table(doc, headers, rows, widths=None, font_size=8.2, first_col_bold=False):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = str(h)
        set_cell_shading(cell, BLUE)
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_font(p, size=font_size, bold=True, color="FFFFFF")
    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            cell.text = str(value)
            set_cell_shading(cell, PALE_BLUE if ridx % 2 else "FFFFFF")
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 and len(str(value)) < 36 else WD_ALIGN_PARAGRAPH.LEFT
                set_paragraph_font(p, size=font_size, bold=(first_col_bold and i == 0))
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def page_break(doc):
    doc.add_page_break()


def build_docx():
    doc = Document()
    style_document(doc)
    props = doc.core_properties
    props.title = "Mode-I Adaptive Remeshing Supervisor Report"
    props.subject = "Pandey-Kumar benchmark reconstruction and mesh-count discrepancy"
    props.author = "Pruthviraja Reddy Vandavagali"

    # Page 1
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(72); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Application of Built in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Phase Field Fracture Simulations")
    font_run(r, size=23, bold=True, color="000000")
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(20)
    r = p.add_run("Mode I Supervisor Report"); font_run(r, size=18, bold=True, color=BLUE)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(16)
    r = p.add_run("17 September 2026"); font_run(r, size=11, color=GRAY)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(80)
    r = p.add_run("Pruthviraja Reddy Vandavagali\nMaster Thesis in Computational Materials Science\nChair of Applied Mechanics IMFD\nTU Bergakademie Freiberg")
    font_run(r, size=11, color="000000")

    # Page 2
    page_break(doc)
    add_heading(doc, "Executive Summary", 1)
    add_body(doc, "The Mode-I benchmark reconstruction now has a verified fixed-mesh response anchor, a verified Abaqus-native pre-refinement workflow, and a causally resolved preprocessing defect. The remaining scientific question is the adaptive mesh count: the canonical project rule with errorTarget=1.0 produces 71,320 finite elements, whereas Pandey and Kumar report 13,941 for their proposed adaptive mesh.")
    add_body(doc, "Important distinction between the two reported element counts. The 26,282-element mesh and the 13,941-element mesh do not represent the mesh before and after one adaptive-remeshing operation. They belong to two separate simulations. In the standard PFM, a manually refined crack-propagation corridor with h=0.003 mm is embedded in a global h=0.02 mm mesh, resulting in 26,282 finite elements. In the proposed adaptive PFM, the analysis starts again from a separate coarse mesh with global h=0.02 mm and no equivalent manually pre-refined corridor. MISESERI then drives native adaptive remeshing to a final mesh of approximately 13,941 elements with local h=0.001 mm. The paper does not report the initial coarse element count for this adaptive route.", bold_lead="Important distinction between the two reported element counts.")
    add_table(doc, ["Result", "Verified value", "Scientific meaning"], [
        ["Published standard PFM", "26,282 elements", "Global h=0.02 mm plus manual h=0.003 mm crack corridor"],
        ["Published proposed adaptive PFM", "13,941 elements", "Separate coarse branch; initial count not reported; local h=0.001 mm after remeshing"],
        ["Project adaptive reconstruction", "2,906 -> 71,320 elements", "Canonical project pre-analysis and errorTarget=1.0"],
        ["Fixed response anchor 1398090", "Fmax=0.757778 kN", "Close agreement with published Mode-I force-displacement response"],
        ["Corrected nominal 1% 1404933", "K0=137.820804 kN/mm", "Stiffness recovered after N_BOTTOM repair"],
    ], widths=[4.3, 4.2, 8.2], font_size=8.1, first_col_bold=True)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4.2)
    r = p.add_run("The reduction from 26,282 to 13,941 must not be interpreted as adaptive remeshing reducing the element count. The correct comparison is between two alternative meshing strategies. For the RemeshingRule used in this study, coarsening is disabled (")
    font_run(r)
    r = p.add_run("coarseningFactor=NOT_ALLOWED")
    font_run(r, size=8.9)
    r.font.name = "Consolas"
    r._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Consolas")
    r._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Consolas")
    r = p.add_run("); therefore the adaptive-remeshing operation is expected to increase, rather than decrease, the finite-element count relative to that adaptive route's own initial coarse mesh.")
    font_run(r)
    add_source(doc, "Pandey and Kumar (2025), Sections 3.3 and 4.1; project Jobs 1398090, 1399632 and 1404933.")

    # Page 3
    page_break(doc)
    add_heading(doc, "Mode I Benchmark and Quantitative Reference", 1)
    add_body(doc, "The benchmark is a 1.0 mm by 1.0 mm square plate with a zero-gap horizontal crack of length a0=0.5 mm along y=0.5 mm. The publication specifies vertical Mode-I loading and lower-edge support. The single ux=0 restraint shown below removes rigid-body motion. A top-edge U1=0 condition is a project reconstruction choice and is not presented as a published condition.")
    doc.add_picture(str(FIG / "mode1_geometry.png"), width=Inches(6.55))
    add_caption(doc, "Figure 1. Mode-I geometry, crack, loading and boundary-condition provenance.")
    doc.add_picture(str(FIG / "force_displacement_full.png"), width=Inches(6.75))
    add_caption(doc, "Figure 2. Full force-displacement comparison. Markers identify each peak; shading shows the project OLS range.")
    add_body(doc, "Published comparison: Pandey and Kumar (2025), Section 4.1 and Figure 7(a), support comparison of the force-displacement response. Project-derived quantity: K0=137.945520 kN/mm is obtained from Job 1398090 by an OLS fit over the first 400 active increments; it is not a stiffness value reported by Pandey and Kumar.", size=8.4)

    # Page 4: Multifaceted Mesh-Convergence Assessment
    page_break(doc)
    add_heading(doc, "Multifaceted Mesh-Convergence Assessment", 1)
    add_body(doc, "Peak load alone is not sufficient to demonstrate mesh convergence in a phase-field fracture model. Mesh adequacy is therefore evaluated using complementary global and spatial quantities: the complete force-displacement response, initial structural stiffness, peak force and displacement at peak, external work over a common displacement interval, phase-field distribution, and crack-path/localization behaviour. Agreement across these measures provides a substantially stronger convergence assessment than comparison of Fmax alone.", bold_lead="Peak load alone is not sufficient to demonstrate mesh convergence in a phase-field fracture model.")
    
    # Table 2a: Multi-Quantity Convergence Criteria (7 rows, no cost)
    add_table(doc, ["Quantity", "Symbol / Range", "Physical / Numerical Role", "Observed Convergence Behaviour"], [
        ["Complete F-u response", "F(u), u >= 0", "Global structural and post-peak softening response", "Required criterion; full five-curve comparison is not claimed because four refined-job curve files are not preserved in the report package"],
        ["Initial stiffness K0", "K0 = dF/du (u <= 1.0 um)", "Elastic compliance before damage onset", "Invariant: 137.95 -> 137.82 kN/mm (0.089% shift across 4.56x FE count)"],
        ["Peak force Fmax", "Fmax = max F(u)", "Regularized structural fracture resistance", "Monotonic decrease with refinement; successive changes generally reduce, but strict asymptotic convergence is not established"],
        ["Displacement at peak", "u(Fmax)", "Deformation threshold for crack initiation", "Monotonic decrease: 5.857 -> 5.575 um; measurable mesh sensitivity remains"],
        ["External work Wext", "int_0^u_common F du", "Global mechanical work from the F-u response", "Monotonic decrease: 2.3583 -> 2.1475 mJ at u_common=6.816 um; no formal convergence order claimed"],
        ["Phase-field distribution", "d(x, u) on ligament", "Regularized spatial damage localization", "Required criterion; quantitative comparison withheld pending auditable five-job x-d and matched-frame extraction files"],
        ["Crack path / profile", "y_crack(x) ~ 0.5 mm", "Spatial trajectory of crack propagation", "Evaluated qualitatively around the symmetry line; no numerical path metric claimed without preserved coordinates"],
    ], widths=[3.8, 3.2, 5.2, 5.5], font_size=7.6, first_col_bold=True)

    # Table 2b: Authoritative Five-Mesh Dataset
    add_table(doc, ["Mesh size h", "Authoritative job", "Elements", "Nodes", "K0 [kN/mm]", "Fmax [kN]", "u(Fmax) [mm]", "Wext [mJ] (u <= 6.82 um)"], [
        ["0.00300 mm", "1401527", "15,192", "15,521", "137.9455", "0.757778", "0.005857", "2.3583"],
        ["0.00200 mm", "1401528", "32,130", "32,613", "137.8941", "0.741194", "0.005711", "2.2480"],
        ["0.00150 mm", "1401529", "41,912", "42,491", "137.8576", "0.732196", "0.005633", "2.1901"],
        ["0.00125 mm", "1402827", "51,408", "52,069", "137.8368", "0.729041", "0.005606", "2.1701"],
        ["0.00100 mm", "1402828", "69,384", "70,179", "137.8233", "0.725460", "0.005575", "2.1475"],
    ], widths=[2.2, 2.3, 2.0, 1.9, 2.3, 2.3, 2.3, 2.4], font_size=7.8, first_col_bold=True)

    doc.add_picture(str(FIG / "fig_convergence_fu_overlay.png"), width=Inches(6.85))
    add_caption(doc, "Figure 3. Verified scalar convergence metrics for the five qualified fixed meshes (Jobs 1401527, 1401528, 1401529, 1402827, and 1402828). No reconstructed force-displacement trajectories are used.")
    add_body(doc, "Do the complete structural responses converge? The elastic response is essentially mesh-independent over the investigated range. Peak force decreases monotonically as 0.757778 -> 0.741194 -> 0.732196 -> 0.729041 -> 0.725460 kN, but the fracture-related response remains mesh-sensitive and strict asymptotic convergence is not established. Because raw complete F-u histories for four refined jobs are not preserved in the report package, a defensible five-curve overlay is not shown and strict full-curve convergence is not claimed. Job 1398090 remains the named response anchor; parallel parity jobs are not double-counted in the sequence.", bold_lead="Do the complete structural responses converge?", size=8.5)

    # Page 5: External Work and Spatial Evidence Status
    page_break(doc)
    add_heading(doc, "External Work and Spatial Evidence Status", 1)
    add_body(doc, "The quantity Wext(u) = int_0^u F(u~) du~ is the external mechanical work obtained from the global reaction-force-displacement response. It is not presented as Abaqus internal energy or fracture energy, because the present UEL does not provide a fully qualified built-in ENERGY balance.", bold_lead="The quantity Wext(u) = int_0^u F(u~) du~ is the external mechanical work")
    add_body(doc, "Because Job 1401528 (h=0.00200 mm) terminated automatically at u_end = 0.006816 mm and Job 1402827 (h=0.00125 mm) at u_end = 0.007208 mm, external work is evaluated over the common displacement interval u in [0, 0.006816 mm] (u <= 6.82 um). Over this common cutoff, Wext decreases monotonically across the five meshes from 2.3583 to 2.1475 mJ. Successive changes become substantially smaller at the finer levels overall, although the final change is slightly larger than the preceding one; therefore no formal asymptotic convergence order is claimed. The reference-only cutoff value of 0.00235865 J (2.35865 mJ) over u <= 0.007670 mm applies to the reference baseline, but cannot be evaluated directly for meshes that terminated earlier.", size=8.8)
    add_body(doc, "Quantitative phase-field and crack-path values are withheld from this supervisor report because the required five-job provenance package is not preserved. Retaining numerical values would require, for every job, the actual extracted x-d pairs, matched step/frame and displacement, crack-path coordinates, extraction settings, and the calculation used for any L2 difference or characteristic front location. Until those artifacts exist, spatial convergence is evaluated qualitatively from localization around the expected y=0.5 mm ligament and is not assigned numerical convergence metrics.", size=8.8)
    doc.add_picture(str(FIG / "fig_convergence_work_and_spatial.png"), width=Inches(6.85))
    add_caption(doc, "Figure 4. Common-interval external work and successive relative changes in peak force and external work. The final refinement step is slightly larger than the preceding step, so no formal convergence order is reported.")
    add_body(doc, "Multifaceted convergence assessment: The initial elastic structural response is essentially mesh-independent, with K0 varying by approximately 0.089% across a 4.56-fold increase in finite-element count. In contrast, Fmax, u(Fmax), and common-interval external work retain measurable mesh sensitivity. Strict asymptotic convergence is not claimed from the peak-load sequence. Phase-field and crack-path convergence remain required parts of mesh adequacy, but quantitative spatial conclusions are deferred until auditable five-job extraction artifacts are preserved.", bold_lead="Multifaceted convergence assessment:")

    # Page 6
    page_break(doc)
    add_heading(doc, "Published Adaptive Workflow", 1)
    add_body(doc, "The paper describes a two-job pre-refinement process. The coarse analysis is converted to the layered UEL/facsimile representation, MISESERI is requested on All_elem, and Abaqus native remeshing generates a separate refined input for the final phase-field solve.")
    doc.add_picture(str(FIG / "published_workflow.png"), width=Inches(6.9))
    add_caption(doc, "Figure 5. Published Job-1 to Job-2 adaptive pre-refinement workflow.")
    add_table(doc, ["Paper reported proposed Mode-I mesh", "Project reconstruction"], [[
        "Initial global size h=0.02 mm\nNo local pre-refinement\nInitial coarse count not reported\nAdaptive local size h=0.001 mm\nFinal adapted count 13,941",
        "Initial coarse pre-analysis 2,906 finite elements\nMISESERI on 2,906 underlying elements\nerrorTarget=1.0\nNative adaptiveRemesh\nFinal adapted count 71,320",
    ]], widths=[8.3, 8.3], font_size=8.8)
    add_body(doc, "The workflow is not a refinement of the 26,282-element standard-PFM mesh. Job-1_UEL belongs to the separate proposed adaptive branch, and Job-2_UEL is the refined result of that branch.", bold_lead="The workflow is not a refinement of the 26,282-element standard-PFM mesh.")
    add_source(doc, "Pandey and Kumar (2025), Section 3.3 and Listings 1-4; project canonical pre-analysis audit.")

    # Page 7
    page_break(doc)
    add_heading(doc, "MISESERI and Uniform Error Sizing", 1)
    add_body(doc, "MISESERI is an Abaqus stress discretization error indicator associated with the recovered von Mises stress field. A relatively large value indicates that the local finite-element stress representation is comparatively under-resolved. Under UNIFORM_ERROR sizing, such regions tend to demand a finer target mesh. Smaller-error regions demand less refinement. Because coarseningFactor=NOT_ALLOWED, the present rule does not use low-error regions to coarsen the mesh.")
    doc.add_picture(str(FIG / "miseseri_concept.png"), width=Inches(6.7))
    add_caption(doc, "Figure 6. Defensible qualitative interpretation of MISESERI under the reported remeshing rule.")
    doc.add_picture(str(ROOT / "docs" / "supervisor_reports" / "17-09-2026" / "MA_ModeI_Supervisor_Meeting_Pack_2026-09-17" / "figures" / "figure_3_2_canonical_miseseri_vs_refined_mesh.png"), width=Inches(6.8))
    add_caption(doc, "Figure 7. Observed project relationship between coarse MISESERI and local size in the native 1% mesh; this is an empirical spatial association, not a universal sizing formula.")
    add_body(doc, "errorTarget=1.0 specifies a 1% target error tolerance under Abaqus UNIFORM_ERROR sizing. It does not mean refine 1% of the elements, and it is not the direct condition MISESERI >= 0.01. Abaqus combines the error field, target tolerance, size bounds, refinement factor and internal sizing logic. The exact internal MISESERI-to-h transformation has not been established from the available documentation or evidence.", size=8.6)

    # Page 8
    page_break(doc)
    add_heading(doc, "Stiffness Anomaly and Boundary Set Repair", 1)
    add_body(doc, "The low-stiffness 71,320-element branch was caused by malformed N_BOTTOM formatting, not by the adaptive mesh or phase-field constitutive response. The original set placed 150 node IDs on one free-format data line; Abaqus retained only the first 16, leaving 134 bottom nodes free vertically.")
    doc.add_picture(str(FIG / "force_displacement_zoom.png"), width=Inches(6.75))
    add_caption(doc, "Figure 8. Initial elastic-range zoom. The corrected model and fixed reference overlap near 138 kN/mm; the defective branch remains near 122.38 kN/mm.")
    doc.add_picture(str(FIG / "boundary_set_flow.png"), width=Inches(6.75))
    add_caption(doc, "Figure 9. Verified preprocessing defect and deterministic repair.")
    add_table(doc, ["Model", "Elements", "K0 [kN/mm]", "Fmax [kN]", "u(Fmax) [mm]"], [
        ["Fixed reference 1398090", "15,192", "137.945520", "0.757778", "0.005857"],
        ["Defective diagnostic 1399632", "71,320", "about 122.38", "0.478203", "0.004150"],
        ["Corrected nominal 1% 1404933", "71,320", "137.820804", "0.745325", "0.005750"],
    ], widths=[5.3, 2.5, 3.2, 2.8, 2.9], font_size=7.8, first_col_bold=True)
    add_body(doc, "A separate frozen-damage requalification, Job 1405044, independently recovered K0=138.021013 kN/mm, confirming that stiffness recovery occurs before fracture evolution.", size=8.4)

    # Page 9
    page_break(doc)
    add_heading(doc, "Abaqus Release Study", 1)
    add_body(doc, "The canonical native remeshing operation was reproduced across the installed Linux releases. The generated adapted topology remained unchanged, so release version does not explain the 71,320-versus-13,941 discrepancy.")
    add_table(doc, ["Abaqus environment", "Adapted finite elements", "Result"], [
        ["Abaqus 2019 Linux", "71,320", "same canonical adapted topology/artifact"],
        ["Abaqus 2021 Linux", "71,320", "same"],
        ["Abaqus 2022 Linux", "71,320", "same"],
        ["Abaqus 2023 Linux", "71,320", "same"],
    ], widths=[5.5, 4.2, 7.4], font_size=8.8, first_col_bold=True)
    add_body(doc, "Within the tested Linux Abaqus 2019-2023 releases, release version does not explain the 71,320-versus-13,941 discrepancy.", bold_lead="Within the tested Linux Abaqus 2019-2023 releases,")
    add_body(doc, "The Abaqus 2019 PBS wrapper had a walltime/logging issue, but the generated remeshing artifact was available and matched the canonical result. Any Windows/Abaqus 2024 observation should be treated separately as a platform-plus-release-confounded sensitivity, not as a clean release comparison.", size=8.8)
    add_heading(doc, "What the release result rules out", 2)
    add_bullets(doc, [
        "A simple Linux release change from 2019 through 2023 does not change the adapted count.",
        "The element-count discrepancy therefore requires a different explanation, such as an unreported modeling, meshing or execution detail.",
        "This conclusion concerns the generated adaptive mesh artifact; it does not claim identity of every solver or scheduler detail.",
    ], size=9.0)

    # Page 10
    page_break(doc)
    add_heading(doc, "Standard PFM versus Proposed Adaptive PFM versus This Reconstruction", 1)
    add_body(doc, "All three lanes address the same Mode-I benchmark, but they are independent discretization strategies. The two paper counts are final counts from different simulations, while the project count pair explicitly shows the before-and-after values within one adaptive route.")
    doc.add_picture(str(FIG / "three_branch_mesh_routes.png"), width=Inches(6.85))
    add_caption(doc, "Figure 10. Independent meshing branches and the only valid within-route count comparisons.")
    add_body(doc, "Do not read this figure horizontally as 26,282 -> 13,941. The branches are independent discretization strategies.", size=9.0)
    add_body(doc, "Paper adaptive route: initial count not reported -> 13,941. Project adaptive route: 2,906 -> 71,320.", bold_lead="Paper adaptive route:")
    add_body(doc, "Abaqus uses MISESERI and the RemeshingRule settings to determine a spatial target-size field. The inputs and resulting mesh are observable, but the exact internal numerical transformation has not been established. The report therefore compares verified input fields, rule parameters, spatial patterns and resulting element counts rather than inventing a direct MISESERI-to-h equation.", size=8.8)

    # Page 11
    page_break(doc)
    add_heading(doc, "Element Count Discrepancy Sensitivity Audit", 1)
    add_body(doc, "The following one-factor tests show how the adapted count responds to controlled changes. Several factors materially change the count, but none reproduces 13,941 while retaining the published Mode-I RemeshingRule settings.", size=8.8)
    ofat = [
        ["Canonical errorTarget=1.0", "71,320", "baseline"],
        ["Abaqus 2019 Linux", "71,320", "release insufficient"],
        ["Abaqus 2021 Linux", "71,320", "release insufficient"],
        ["Abaqus 2022 Linux", "71,320", "release insufficient"],
        ["Abaqus 2023 Linux", "71,320", "release insufficient"],
        ["outputFrequency=LAST_INCREMENT", "71,320", "no effect"],
        ["refinementFactor=3", "47,428", "substantial effect; insufficient"],
        ["coarsening enabled/default", "71,037", "negligible"],
        ["minimum-size specification removed", "71,320", "no effect"],
        ["maximum-size specification removed", "70,736", "negligible"],
        ["coarse global seed 0.03 mm", "48,919", "substantial but insufficient"],
        ["top-edge U1 released", "55,761", "substantial but insufficient"],
        ["CPE4 to CPE4R", "103,706", "wrong direction"],
        ["CPS4 branch", "58,679", "confounded formulation sensitivity"],
        ["errorTarget=2.0", "17,687", "sensitivity only; not evidence paper used 2%"],
        ["errorTarget=3.0", "8,120", "sensitivity only"],
        ["errorTarget=5.0", "4,356", "sensitivity only"],
    ]
    add_table(doc, ["One-factor test", "Adapted finite elements", "Interpretation"], ofat, widths=[7.0, 3.8, 6.2], font_size=7.25, first_col_bold=True)
    add_body(doc, "Element-count proximity alone cannot identify the paper's executed setting. In particular, the 2%, 3% and 5% branches are sensitivity results; they do not show that Pandey and Kumar used a different errorTarget from the published value of 1.0.", size=8.3)

    # Page 10
    page_break(doc)
    add_heading(doc, "Remaining Mode I Discrepancy and Current Scientific Conclusion", 1)
    add_body(doc, "The canonical reconstruction produces 71,320 finite elements whereas Pandey and Kumar report 13,941 for their proposed Mode-I adaptive mesh. Abaqus release, output frequency, top lateral constraint, element formulation, global seed, coarsening, refinement factor, sizing bounds and error-target sensitivities have been investigated. Several parameters materially change the mesh count, but no tested case reproduces 13,941 while simultaneously preserving the retained published Mode-I RemeshingRule settings. The exact source of the discrepancy therefore remains unresolved.")
    add_heading(doc, "Conclusions", 2)
    add_bullets(doc, [
        "The fixed reference reproduces the published Mode-I force-displacement response closely.",
        "The paper's 26,282-element standard mesh and 13,941-element adaptive mesh are separate branches, not the before-and-after states of one remeshing operation.",
        "The low-stiffness 71,320 branch was caused by malformed N_BOTTOM formatting and is resolved.",
        "The corrected 71,320-element model recovers K0 but retains a modest peak-response difference.",
        "Canonical 1% native remeshing gives 71,320 elements versus the paper's 13,941.",
        "Abaqus 2019-2023 does not explain the discrepancy.",
        "Multiple controlled sensitivities alter the adapted count but do not establish the reported 13,941 configuration.",
        "The remaining element-count discrepancy is the unresolved Mode-I reproduction question.",
    ], size=9.1)
    add_table(doc, ["Comparison", "Initial adaptive-branch count", "Final adapted count"], [
        ["Pandey-Kumar adaptive route", "not reported", "13,941"],
        ["Project adaptive route", "2,906", "71,320"],
    ], widths=[7.0, 5.0, 4.8], font_size=8.7, first_col_bold=True)

    # Page 11
    page_break(doc)
    add_heading(doc, "References", 1)
    refs = [
        "Pandey, A. and Kumar, S. (2025). A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture. Computer Modeling in Engineering and Sciences, 144(3), 3251-3286. https://doi.org/10.32604/cmes.2025.067858.",
        "Molnar, G. and Gravouil, A. (2017). 2D and 3D Abaqus implementation of a robust staggered phase-field solution for modeling brittle fracture. Finite Elements in Analysis and Design, 130, 27-38. https://doi.org/10.1016/j.finel.2017.03.002.",
        "Msekh, M. A., Sargado, J. M., Jamshidian, M., Areias, P. M. and Rabczuk, T. (2015). Abaqus implementation of phase-field model for brittle fracture. Computational Materials Science, 96, 472-484. https://doi.org/10.1016/j.commatsci.2014.05.071.",
        "Dassault Systemes. Abaqus 2023 Documentation. Analysis User's Guide, Theory Guide and input syntax documentation for adaptive remeshing and stress error indicators.",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.55); p.paragraph_format.first_line_indent = Cm(-0.55); p.paragraph_format.space_after = Pt(8)
        r = p.add_run(f"{i}. {ref}"); font_run(r, size=9.4)
    add_heading(doc, "Primary Project Evidence", 2)
    add_bullets(doc, [
        "Job 1398090 fixed response anchor and project OLS stiffness extraction.",
        "Job 1399632 defective preprocessing diagnostic and N_BOTTOM warning evidence.",
        "Job 1404933 corrected nominal-1% full-fracture response.",
        "Job 1405044 frozen-damage stiffness requalification.",
        "Canonical 2,906-element MISESERI pre-analysis and native 71,320-element adapted artifact.",
        "Controlled Abaqus 2019-2023 release study and one-factor mesh-count sensitivity records.",
    ], size=9.0)
    add_body(doc, "All job identifiers and numerical values in this report refer to project-controlled extraction artifacts. No element count, stiffness value or internal Abaqus sizing law has been inferred beyond the recorded evidence.", size=8.6)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    make_geometry()
    make_response_figures()
    make_convergence_figures()
    make_workflow()
    make_miseseri_concept()
    make_boundary_flow()
    make_branch_diagram()
    build_docx()
