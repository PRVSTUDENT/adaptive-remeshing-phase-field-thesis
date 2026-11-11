# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/visualizer.py
========================================
Publication-quality scientific visualization generator for the
Reusable Method A Adaptive-Remeshing Framework.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PolyCollection, LineCollection
import numpy as np


class FrameworkVisualizer(object):
    """
    Renders standalone publication figures (300 DPI PNG & vector PDF)
    from validated simulation data and finite-element meshes.
    """

    def __init__(self, config):
        self.config = config

    def plot_coarse_vs_adapted_mesh(self, coarse_nodes, coarse_elems, adapted_nodes, adapted_elems, out_png, out_pdf=None):
        """
        Renders side-by-side coarse vs adapted mesh wireframes.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        for ax, nodes, elems, title in [
            (ax1, coarse_nodes, coarse_elems, "Coarse Mesh (%d elements)" % len(elems)),
            (ax2, adapted_nodes, adapted_elems, "Adaptive Mesh (%d elements)" % len(elems))
        ]:
            polys = []
            for eid, enodes in elems.items():
                pts = [nodes[n] for n in enodes if n in nodes]
                if len(pts) >= 3:
                    polys.append(pts)

            pcoll = PolyCollection(polys, facecolors="white", edgecolors="#1e293b", linewidths=0.35)
            ax.add_collection(pcoll)
            ax.set_aspect("equal")
            ax.set_xlim(-0.02, 1.02)
            ax.set_ylim(-0.02, 1.02)
            ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
            ax.set_xlabel("x [mm]", fontsize=10)
            ax.set_ylabel("y [mm]", fontsize=10)
            ax.grid(True, linestyle=":", alpha=0.4)

        plt.tight_layout()
        plt.savefig(out_png, dpi=300)
        if out_pdf:
            plt.savefig(out_pdf)
        plt.close(fig)
        return out_png

    def plot_force_displacement(self, fu_data, ref_data=None, out_png="", out_pdf=None, benchmark_title=""):
        """
        Plots the extracted force-displacement curve against an optional reference benchmark.
        fu_data: list of (u, F) tuples.
        ref_data: optional list of (u, F) tuples.
        """
        fig, ax = plt.subplots(figsize=(8, 6))

        u_vals = [pt[0] for pt in fu_data]
        f_vals = [pt[1] for pt in fu_data]

        ax.plot(u_vals, f_vals, color="#1e3a8a", linewidth=2.0, label="Method A (Simulated)")

        if ref_data:
            ref_u = [pt[0] for pt in ref_data]
            ref_f = [pt[1] for pt in ref_data]
            ax.plot(ref_u, ref_f, "r--", linewidth=1.8, label="Reference Benchmark")

        ax.set_xlabel("Displacement $u_y$ [mm]", fontsize=12)
        ax.set_ylabel("Tensile Reaction Force $F$ [kN]", fontsize=12)
        title = benchmark_title or "Force-Displacement Response"
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(frameon=True, loc="upper right")

        plt.tight_layout()
        if out_png:
            plt.savefig(out_png, dpi=300)
        if out_pdf:
            plt.savefig(out_pdf)
        plt.close(fig)
        return out_png

    def plot_energy_balance(self, energy_records, out_png="", out_pdf=None):
        """
        Plots elastic strain energy and fracture dissipation vs displacement.
        """
        fig, ax = plt.subplots(figsize=(8, 6))

        u_vals = [r["displacement_mm"] for r in energy_records]
        e_elas = [r["elastic_energy_kNmm"] for r in energy_records]
        e_frac = [r["fracture_energy_kNmm"] for r in energy_records]
        e_tot = [r["total_energy_kNmm"] for r in energy_records]

        ax.plot(u_vals, e_elas, color="#2563eb", linewidth=1.8, label="Elastic Strain Energy $E_{elas}$")
        ax.plot(u_vals, e_frac, color="#dc2626", linewidth=1.8, label="Fracture Dissipation $E_{frac}$")
        ax.plot(u_vals, e_tot, "k--", linewidth=1.5, label="Total Internal Energy $E_{tot}$")

        ax.set_xlabel("Displacement $u_y$ [mm]", fontsize=12)
        ax.set_ylabel("Energy [$kN\\cdot mm$ = J]", fontsize=12)
        ax.set_title("Domain Thermodynamic Energy Evolution", fontsize=13, fontweight="bold", pad=12)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(frameon=True, loc="upper left")

        plt.tight_layout()
        if out_png:
            plt.savefig(out_png, dpi=300)
        if out_pdf:
            plt.savefig(out_pdf)
        plt.close(fig)
        return out_png
