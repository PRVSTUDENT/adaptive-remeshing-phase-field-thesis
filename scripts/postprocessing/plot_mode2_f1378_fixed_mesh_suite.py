"""Plotting script for Mode-II Gate M2-1B 4-Tier Fixed-Mesh Convergence Suite.

Generates 4-panel publication-quality figure:
- Panel A: Mesh discretization scaling h and h/l0 across 4 tiers
- Panel B: Computational scale: Physical elements, layered elements, and solver DOFs
- Panel C: Structural stiffness convergence K0(h) vs paper benchmark (45.68 kN/mm)
- Panel D: Epistemological Decision Tree (Possibility A vs Possibility B)
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generate_figure(out_pdf, out_png):
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    plt.subplots_adjust(hspace=0.32, wspace=0.28)
    
    # Data for the 4 tiers
    tiers = ['Tier 1\n(Coarse)', 'Tier 2\n(Medium)', 'Tier 3\n(Interm.)', 'Tier 4\n(Fine)']
    nx_ny = [50, 134, 200, 268]
    h_um = [20.0, 7.46, 5.00, 3.73]
    h_over_l0 = [20.0 / 15.0, 7.46 / 15.0, 5.00 / 15.0, 3.73 / 15.0]
    n_phys_elem = [2500, 17956, 40000, 71824]
    n_layers_elem = [7500, 53868, 120000, 215472]
    n_dofs = [7828, 54807, 121301, 217435]
    k0_measured = [45.7688, 45.9638, 45.8597, 45.8511]
    k0_target = 45.68
    
    # ----------------------------------------------------
    # Panel A: Spatial Resolution Scaling h & h/l0
    # ----------------------------------------------------
    ax = axes[0, 0]
    color_bar = '#2b5c8f'
    bars = ax.bar(tiers, h_um, color=color_bar, width=0.55, edgecolor='black', linewidth=1.2, zorder=3)
    ax.axhline(15.0, color='#d95f02', linestyle='--', linewidth=1.8, label=r'Length scale $l_0 = 15\,\mu\mathrm{m}$')
    ax.axhline(7.5, color='#7570b3', linestyle=':', linewidth=1.6, label=r'$l_0 / 2 = 7.5\,\mu\mathrm{m}$')
    ax.axhline(3.75, color='#1b9e77', linestyle='-.', linewidth=1.6, label=r'$l_0 / 4 = 3.75\,\mu\mathrm{m}$')
    
    for bar, h, ratio in zip(bars, h_um, h_over_l0):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.6,
                f'{h:.2f} $\\mu$m\n({ratio:.2f} $l_0$)',
                ha='center', va='bottom', fontsize=9.5, fontweight='bold')
        
    ax.set_ylabel(r'Element Size $h$ [$\mu\mathrm{m}$]', fontsize=11, fontweight='bold')
    ax.set_title(r'(a) Spatial Discretization Scaling ($l_0 = 15\,\mu\mathrm{m}$)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 25)
    ax.grid(axis='y', linestyle=':', alpha=0.6, zorder=0)
    ax.legend(loc='upper right', fontsize=9.5, framealpha=0.9)
    
    # ----------------------------------------------------
    # Panel B: Computational Scale & Problem Size
    # ----------------------------------------------------
    ax = axes[0, 1]
    x_pos = np.arange(len(tiers))
    width = 0.35
    
    b1 = ax.bar(x_pos - width/2, [n/1000.0 for n in n_phys_elem], width, label='Physical Quads [k]',
                color='#377eb8', edgecolor='black', linewidth=1.1, zorder=3)
    b2 = ax.bar(x_pos + width/2, [n/1000.0 for n in n_dofs], width, label='Active Equations / DOFs [k]',
                color='#e41a1c', edgecolor='black', linewidth=1.1, zorder=3)
    
    for b in b1:
        ax.text(b.get_x() + b.get_width()/2.0, b.get_height() + 3.0,
                f'{b.get_height():.1f}k', ha='center', va='bottom', fontsize=9)
    for b in b2:
        ax.text(b.get_x() + b.get_width()/2.0, b.get_height() + 3.0,
                f'{b.get_height():.1f}k', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    ax.set_xticks(x_pos)
    ax.set_xticklabels(tiers)
    ax.set_ylabel('Count [Thousands]', fontsize=11, fontweight='bold')
    ax.set_title(r'(b) Computational Problem Size ($2.5\mathrm{k} \to 71.8\mathrm{k}$ FEs)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 260)
    ax.grid(axis='y', linestyle=':', alpha=0.6, zorder=0)
    ax.legend(loc='upper left', fontsize=9.5, framealpha=0.9)
    
    # ----------------------------------------------------
    # Panel C: Initial Elastic Stiffness Convergence K0(h)
    # ----------------------------------------------------
    ax = axes[1, 0]
    h_vals = [20.0, 7.46, 5.00, 3.73]
    
    ax.plot(h_vals, k0_measured, 'o-', color='#1b9e77', linewidth=2.2, markersize=8,
            label=r'Measured $K_0(h)$ from Abaqus Datacheck', zorder=4)
    ax.axhline(k0_target, color='black', linestyle='--', linewidth=1.6,
               label=r'Target $K_0 = 45.68\,\mathrm{kN/mm}$ (Pandey & Kumar / Navidtehrani)')
    ax.axhspan(k0_target * 0.99, k0_target * 1.01, color='green', alpha=0.15,
               label=r'$\pm 1.0\%$ Acceptance Corridor')
    
    for x, y in zip(h_vals, k0_measured):
        err = (y - k0_target) / k0_target * 100.0
        ax.annotate(f'{y:.2f} kN/mm\n({err:+.2f}%)',
                    (x, y), textcoords='offset points', xytext=(0, 12),
                    ha='center', fontsize=9.5, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='none'))
        
    ax.set_xlabel(r'Element Sizing $h$ [$\mu\mathrm{m}$]', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Initial Stiffness $K_0$ [$\mathrm{kN/mm}$]', fontsize=11, fontweight='bold')
    ax.set_title(r'(c) Initial Stiffness Parity ($<0.65\%$ error across all tiers)', fontsize=12, fontweight='bold')
    ax.set_xlim(22, 2)  # Reverse x-axis so refinement proceeds to the right
    ax.set_ylim(44.5, 47.0)
    ax.grid(True, linestyle=':', alpha=0.6, zorder=0)
    ax.legend(loc='lower left', fontsize=9.5, framealpha=0.9)
    
    # ----------------------------------------------------
    # Panel D: Epistemological Decision Tree
    # ----------------------------------------------------
    ax = axes[1, 1]
    ax.axis('off')
    
    # Box for Hypothesis / Gate M2-1B
    box_props_top = dict(boxstyle='round,pad=0.5', facecolor='#f0f4f8', edgecolor='#2b5c8f', linewidth=1.5)
    box_props_a = dict(boxstyle='round,pad=0.5', facecolor='#e8f5e9', edgecolor='#2e7d32', linewidth=1.5)
    box_props_b = dict(boxstyle='round,pad=0.5', facecolor='#ffebee', edgecolor='#c62828', linewidth=1.5)
    
    ax.text(0.5, 0.92,
            "GATE M2-1B: FIXED-MESH SPATIAL CONVERGENCE\n"
            "Boundary Value Problem: $u_y = 0$, $E=210$ GPa, $\\nu=0.3$, $G_c=2.7$ N/mm, $l_0=15$ $\\mu$m",
            ha='center', va='center', transform=ax.transAxes, fontsize=10.5, fontweight='bold',
            bbox=box_props_top)
    
    # Arrow down
    ax.annotate('', xy=(0.5, 0.76), xytext=(0.5, 0.83),
                arrowprops=dict(arrowstyle="->", color='#333333', lw=1.5))
    
    ax.text(0.5, 0.74, "As $h \\to 0$ ($20 \\to 3.73\\,\\mu\\mathrm{m}$), does $F_{\\max}(h)$ converge to:",
            ha='center', va='center', transform=ax.transAxes, fontsize=10.5, fontstyle='italic')
    
    # Split arrows
    ax.annotate('', xy=(0.25, 0.58), xytext=(0.45, 0.70),
                arrowprops=dict(arrowstyle="->", color='#2e7d32', lw=2.0))
    ax.annotate('', xy=(0.75, 0.58), xytext=(0.55, 0.70),
                arrowprops=dict(arrowstyle="->", color='#c62828', lw=2.0))
    
    # Possibility A Box
    ax.text(0.25, 0.35,
            "POSSIBILITY A:\n"
            "SOLVER CONCURRENCE\n"
            "($F_{\\max} \\to 410\\text{--}415$ N)\n\n"
            r"$\bullet$ Fixed mesh reproduces $\sim 412$ N" "\n"
            r"$\bullet$ Proves adaptive remeshing is accurate" "\n"
            r"$\bullet$ Literature discrepancy is external" "\n"
            r"$\bullet$ Mathematical formulation verified",
            ha='center', va='center', transform=ax.transAxes, fontsize=9.5,
            bbox=box_props_a)
    
    # Possibility B Box
    ax.text(0.75, 0.35,
            "POSSIBILITY B:\n"
            "ADAPTIVE FAILURE\n"
            "($F_{\\max} \\to 360\\text{--}370$ N)\n\n"
            r"$\bullet$ Fixed mesh converges to $\sim 365$ N" "\n"
            r"$\bullet$ Proves adaptive remeshing failed" "\n"
            r"$\bullet$ Refinement corridor too narrow" "\n"
            r"$\bullet$ Over-stiffening artifact isolated",
            ha='center', va='center', transform=ax.transAxes, fontsize=9.5,
            bbox=box_props_b)
    
    ax.set_title('(d) Epistemological Falsification Matrix', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(out_pdf, dpi=300)
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"Generated figures:\n  {out_pdf}\n  {out_png}")

if __name__ == '__main__':
    pdf_path = os.path.abspath('results/figures/mode2/fig_mode2_f1378_fixed_mesh_suite.pdf')
    png_path = os.path.abspath('results/figures/mode2/fig_mode2_f1378_fixed_mesh_suite.png')
    generate_figure(pdf_path, png_path)
