#!/usr/bin/env python3
"""Approximate digitization of Molnar Fig. 7 lc=0.0075 mm curve.

The extraction is intentionally conservative: it keeps the rendered-page pixel
points as raw evidence and writes a separately binned processed curve. The
result is an approximate published-reference trace, not author data.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


PAGE = 6
RENDER_DPI = 300
CROP_BOX = (250, 1050, 1100, 1650)
CALIBRATION = {
    "plot_x0_px": 66.0,
    "plot_xmax_px": 842.0,
    "plot_y0_px": 518.0,
    "plot_y_1p2_px": 61.0,
    "x0_mm": 0.0,
    "xmax_mm": 0.007,
    "y0_kN": 0.0,
    "y_1p2_kN": 1.2,
}


def data_from_pixel(x_px: float, y_px: float) -> tuple[float, float]:
    x = (x_px - CALIBRATION["plot_x0_px"]) / (
        CALIBRATION["plot_xmax_px"] - CALIBRATION["plot_x0_px"]
    ) * CALIBRATION["xmax_mm"]
    y = (CALIBRATION["plot_y0_px"] - y_px) / (
        CALIBRATION["plot_y0_px"] - CALIBRATION["plot_y_1p2_px"]
    ) * CALIBRATION["y_1p2_kN"]
    return x, y


def render_page(pdf: Path, render_dir: Path) -> Path:
    render_dir.mkdir(parents=True, exist_ok=True)
    prefix = render_dir / "molnar_page6"
    png = render_dir / "molnar_page6-06.png"
    if not png.exists():
        subprocess.run(
            [
                "pdftoppm",
                "-f",
                str(PAGE),
                "-l",
                str(PAGE),
                "-r",
                str(RENDER_DPI),
                "-png",
                str(pdf),
                str(prefix),
            ],
            check=True,
        )
    return png


def extract_red_curve(page_png: Path, out_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    image = Image.open(page_png).convert("RGB").crop(CROP_BOX)
    out_dir.mkdir(parents=True, exist_ok=True)
    image.save(out_dir / "fig7_lc_0p0075_crop_300dpi.png")
    pixels = np.asarray(image)
    red_mask = (
        (pixels[:, :, 0] > 170)
        & (pixels[:, :, 1] < 130)
        & (pixels[:, :, 2] < 130)
    )
    ys, xs = np.where(red_mask)
    plot_mask = (xs >= 66) & (xs <= 842) & (ys >= 22) & (ys <= 535)
    legend_rejection = ~((xs < 250) & (ys < 300))
    curve_mask = plot_mask & legend_rejection
    xs = xs[curve_mask]
    ys = ys[curve_mask]

    raw_rows: list[dict[str, str]] = []
    for i, (x_px, y_px) in enumerate(sorted(zip(xs.tolist(), ys.tolist()))):
        u, force = data_from_pixel(float(x_px), float(y_px))
        if -0.00005 <= u <= 0.00705 and -0.02 <= force <= 1.25:
            raw_rows.append(
                {
                    "point_id": str(i + 1),
                    "pixel_x": f"{x_px}",
                    "pixel_y": f"{y_px}",
                    "u_mm": f"{u:.8f}",
                    "reaction_force_kN": f"{force:.8f}",
                    "source": "red_pixel_threshold_300dpi",
                }
            )

    bins: dict[int, list[tuple[float, float]]] = {}
    for row in raw_rows:
        u = float(row["u_mm"])
        force = float(row["reaction_force_kN"])
        key = round(u / 0.00005)
        bins.setdefault(key, []).append((u, force))

    processed_rows: list[dict[str, str]] = []
    for key in sorted(bins):
        values = bins[key]
        u = float(np.median([item[0] for item in values]))
        force = float(np.median([item[1] for item in values]))
        if 0.0 <= u <= 0.00675 and 0.0 <= force <= 0.80:
            processed_rows.append(
                {
                    "point_id": str(len(processed_rows) + 1),
                    "u_mm": f"{u:.8f}",
                    "reaction_force_kN": f"{force:.8f}",
                    "bin_width_mm": "0.00005",
                    "raw_points_in_bin": str(len(values)),
                    "processing": "median_pixel_bin_no_smoothing",
                }
            )
    return raw_rows, processed_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise RuntimeError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_metadata(path: Path, raw_rows: list[dict[str, str]], processed_rows: list[dict[str, str]]) -> None:
    path.write_text(
        "\n".join(
            [
                "# Fig. 7 Digitization Metadata - lc = 0.0075 mm",
                "",
                "Classification: `approximate_published_reference`",
                "",
                "- Paper: Molnar and Gravouil (2017), Finite Elements in Analysis and Design 130, 27-38.",
                "- Local source: `Literature review/1-s2.0-S0168874X16304954-main.pdf`.",
                "- Page and figure: journal page 32, local PDF page 6, Fig. 7.",
                "- Selected curve: Molnar `lc = 0.0075 mm`, red dashed line.",
                "- Visual identification: red dashed curve in the legend and plotted curve; separated from blue dotted and black solid curves by color threshold.",
                "- Axis quantities: horizontal displacement `u [mm]`; vertical reaction force `F [kN]`.",
                f"- Calibration points: x origin ({CALIBRATION['plot_x0_px']}, {CALIBRATION['plot_y0_px']}) -> 0.000 mm; x right ({CALIBRATION['plot_xmax_px']}, {CALIBRATION['plot_y0_px']}) -> 0.007 mm; y origin ({CALIBRATION['plot_x0_px']}, {CALIBRATION['plot_y0_px']}) -> 0.0 kN; y tick ({CALIBRATION['plot_x0_px']}, {CALIBRATION['plot_y_1p2_px']}) -> 1.2 kN.",
                "- Digitization software/script: `scripts/postprocessing/digitize_molnar_fig7_lc_0p0075.py`; Poppler `pdftoppm` render at 300 dpi; Pillow/numpy red-pixel threshold.",
                f"- Raw points: {len(raw_rows)}.",
                f"- Processed points: {len(processed_rows)}.",
                "- Peak and post-peak treatment: retained red pixels in the steep drop; processed curve uses median bins without smoothing.",
                "- Overlapping-curve regions: pre-peak branch overlaps other Molnar curves and Miehe symbols; red-pixel evidence is sparse there.",
                "- Estimated coordinate uncertainty: approximately +/-0.00004 mm in displacement and +/-0.015 kN in reaction force, increased near the post-peak drop and symbol overlaps.",
                "- Omitted segments: no red-pixel segment was manually omitted, but legend red pixels were rejected by crop-coordinate filtering.",
                "- Important limitation: these coordinates are not exact author data and must not be used as an exact pass/fail reference.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default="Literature review/1-s2.0-S0168874X16304954-main.pdf")
    parser.add_argument(
        "--out-dir",
        default="references/derived/molnar_gravouil_2017/paper_matched_single_notch",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    page = render_page(Path(args.pdf), Path("tmp/pdfs"))
    raw_rows, processed_rows = extract_red_curve(page, out_dir)
    write_csv(out_dir / "fig7_lc_0p0075_raw.csv", raw_rows)
    write_csv(out_dir / "fig7_lc_0p0075_processed.csv", processed_rows)
    write_metadata(out_dir / "FIG7_DIGITIZATION_METADATA.md", raw_rows, processed_rows)
    print(f"raw_points={len(raw_rows)}")
    print(f"processed_points={len(processed_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
