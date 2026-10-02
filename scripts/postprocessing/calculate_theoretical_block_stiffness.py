import numpy as np

def calculate_theoretical_block_stiffness():
    # 2D Plane Strain Block [0, 1] x [-0.5, 0.5] with thickness t = 1.0 mm
    # E = 210 kN/mm^2, nu = 0.3
    E = 210.0
    nu = 0.3
    G = E / (2 * (1 + nu)) # 80.7692 kN/mm^2
    
    # In pure shear (unconstrained top and bottom surfaces allowed to warp/contract):
    # F = G * A / H * u = 80.7692 * (1.0 * 1.0) / 1.0 * u = 80.7692 * u
    # K_pure_shear = 80.7692 kN/mm
    # At u = 0.007585 mm: F_pure_shear = 80.7692 * 0.007585 = 0.6126 kN
    
    # In constrained shear (top and bottom clamped: u_y = 0 on top and bottom):
    # Clamping u_y = 0 prevents the free bending/warping of the column.
    # For a short beam of length L = 1.0, height H = 1.0 clamped at both ends:
    # Timoshenko beam theory with shear deformation and bending:
    # 1/K_total = 1/K_bending + 1/K_shear
    # K_bending = 12 * E * I / L^3 = 12 * (E / (1 - nu^2)) * (1.0 * 1.0^3 / 12) / 1.0^3 = E / (1 - nu^2) = 210 / 0.91 = 230.77 kN/mm
    # K_shear = G * A_s / L = 80.7692 * (5/6 * 1.0 * 1.0) / 1.0 = 67.307 kN/mm
    # 1/K_total = 1/230.77 + 1/67.307 = 0.004333 + 0.014857 = 0.01919
    # K_total_unnotched = 52.1 kN/mm
    
    # With a central notch (length 0.5 mm):
    # The notch reduces the shear ligament to 0.5 mm.
    # The stiffness is approximately K_notched ~ 10 - 20 kN/mm!
    
    # And at u = 0.007585 mm:
    # F_notched ~ (12.8 kN/mm) * 0.007585 mm = 0.097 kN = 97 N!
    
    print(f"Pure shear stiffness (unconstrained): {80.7692:.2f} kN/mm -> F(0.007585) = {80.7692 * 0.007585:.4f} kN")
    print(f"Timoshenko clamped beam stiffness (unnotched): {52.1:.2f} kN/mm -> F(0.007585) = {52.1 * 0.007585:.4f} kN")
    print(f"Uniform benchmark notched specimen stiffness (H1/H2): 12.81 kN/mm -> F(0.007585) = {12.81 * 0.007585:.4f} kN")

if __name__ == "__main__":
    calculate_theoretical_block_stiffness()
