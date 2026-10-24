import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import minimize

sys.path.insert(0, ".")
from scripts.validation.test_bound_constrained_h1_projection import (
    A_energy, rhs_energy, d_ckpt, n_c5_nodes, c5_nodes, c5_elements,
    compute_energies, solve_elasticity_rf, DONOR_RF2_N, DONOR_E_FRAC_MJ
)

print("Solving box-constrained QP using L-BFGS-B...")
# Objective: f(d) = 1/2 d^T A d - b^T d
# Gradient:  g(d) = A d - b

def loss_and_grad(d):
    Ad = A_energy.dot(d)
    val = 0.5 * np.dot(d, Ad) - np.dot(rhs_energy, d)
    grad = Ad - rhs_energy
    return val, grad

# Bounds: d_ckpt <= d <= 1.0
bounds = [(float(d_ckpt[i]), 1.0) for i in range(n_c5_nodes)]
d0 = d_ckpt.copy()

res = minimize(
    loss_and_grad,
    d0,
    method="L-BFGS-B",
    jac=True,
    bounds=bounds,
    options={"ftol": 1e-15, "gtol": 1e-8, "maxiter": 500, "disp": True}
)

d_opt = res.x
print(f"L-BFGS-B Success: {res.success}, Iterations: {res.nit}, Status: {res.message}")
print(f"d_opt bounds: min={np.min(d_opt):.8f}, max={np.max(d_opt):.8f}")

# Verify exact bounds:
min_margin = np.min(d_opt - d_ckpt)
max_margin = np.max(d_opt - 1.0)
print(f"Bound margins: min(d - d_ckpt) = {min_margin:.2e}, max(d - 1.0) = {max_margin:.2e}")
assert min_margin >= -1e-12, "Lower bound violated!"
assert max_margin <= 1e-12, "Upper bound violated!"

# KKT Check:
grad_opt = A_energy.dot(d_opt) - rhs_energy
# At lower bound (d == d_ckpt): grad >= 0
# At upper bound (d == 1.0): grad <= 0
# Free (d_ckpt < d < 1.0): grad == 0
is_lower = np.abs(d_opt - d_ckpt) < 1e-6
is_upper = np.abs(d_opt - 1.0) < 1e-6
is_free = ~(is_lower | is_upper)

print(f"Active lower (locked to d_ckpt): {np.sum(is_lower)} nodes")
print(f"Active upper (locked to 1.0):    {np.sum(is_upper)} nodes")
print(f"Free advancing nodes:            {np.sum(is_free)} nodes")

lower_mult_viol = np.sum(grad_opt[is_lower] < -1e-5)
upper_mult_viol = np.sum(grad_opt[is_upper] > 1e-5)
free_res_norm = np.max(np.abs(grad_opt[is_free])) if np.sum(is_free) > 0 else 0.0

print(f"KKT Stationarity:")
print(f"  Lower multiplier violations (grad < 0 on lower bound): {lower_mult_viol}")
print(f"  Upper multiplier violations (grad > 0 on upper bound): {upper_mult_viol}")
print(f"  Free gradient inf-norm: {free_res_norm:.6e}")

# Compute Energies and RF2
en = compute_energies(c5_nodes, c5_elements, d_opt)
rf2, _ = solve_elasticity_rf(c5_nodes, c5_elements, d_opt)

e_err = (en["e_total_mJ"] - DONOR_E_FRAC_MJ) / DONOR_E_FRAC_MJ * 100.0
rf_err = (rf2 - DONOR_RF2_N) / DONOR_RF2_N * 100.0

print(f"\n=======================================================")
print(f"   PHYSICALLY ADMISSIBLE H^1 STATE TRANSFER RESULTS   ")
print(f"=======================================================")
print(f"  Fracture Energy: {en['e_total_mJ']:.6f} mJ (Error vs Abaqus: {e_err:+.4f}%)")
print(f"    Potential Energy: {en['e_pot_kNmm']*1000.0:.6f} mJ")
print(f"    Gradient Energy:  {en['e_grad_kNmm']*1000.0:.6f} mJ")
print(f"  Reaction Force:  {rf2:.4f} N (Error vs Abaqus: {rf_err:+.4f}%)")
print(f"  Gate E_frac (<= 2.0%): {'PASS' if abs(e_err) <= 2.0 else 'FAIL'}")
print(f"  Gate RF2 (<= 5.0%):    {'PASS' if abs(rf_err) <= 5.0 else 'FAIL'}")
print(f"  Zero Healing:          PASS (min margin: {min_margin:.2e} >= 0)")
print(f"  Zero Overshoot:        PASS (max margin: {max_margin:.2e} <= 0)")
print(f"=======================================================")
