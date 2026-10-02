import numpy as np

# Coordinates of element 4895 nodes: 824, 979, 1017, 825
# Let's get the exact coordinates of these nodes from M2STATE_FRACFIX_RESTART1R1R7.inp

from pathlib import Path
p = Path('models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7/M2STATE_FRACFIX_RESTART1R1R7.inp')
lines = p.read_text().splitlines()

nodes = {}
in_nodes = False
for l in lines:
    if l.startswith('*NODE'):
        in_nodes = True
        continue
    if in_nodes:
        if l.startswith('*'):
            break
        parts = [float(x.strip()) for x in l.split(',') if x.strip()]
        if len(parts) >= 3:
            nodes[int(parts[0])] = (parts[1], parts[2])

conn = [824, 979, 1017, 825]
coords = np.array([nodes[n] for n in conn]).T # shape (2, 4)
print("Element 4895 Node coords (2x4):\n", coords)

# Material parameters
E_MOD = 210.0
E_NU = 0.3
E_K = 1.0e-7
D_VAL = 0.0 # undamaged
DEG = (1.0 - D_VAL)**2 + E_K

C11 = E_MOD*(1.0 - E_NU)/((1.0 + E_NU)*(1.0 - 2.0*E_NU)) * DEG
C12 = E_MOD*E_NU/((1.0 + E_NU)*(1.0 - 2.0*E_NU)) * DEG
C22 = C11
C33 = E_MOD/(2.0*(1.0 + E_NU)) * DEG

D_ELAS = np.array([
    [C11, C12, 0.0],
    [C12, C22, 0.0],
    [0.0, 0.0, C33]
])

print(f"C11 = {C11:.4f}, C12 = {C12:.4f}, C33 = {C33:.4f}")

# Integration points (2x2 Gauss)
xg4 = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
yg4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]
w4 = [1.0, 1.0, 1.0, 1.0]

K_elem = np.zeros((8, 8))

for kpt in range(4):
    xi = xg4[kpt]
    eta = yg4[kpt]
    wt = w4[kpt]

    D_N = np.array([
        [-0.25*(1-eta),  0.25*(1-eta), 0.25*(1+eta), -0.25*(1+eta)],
        [-0.25*(1-xi),  -0.25*(1+xi),  0.25*(1+xi),   0.25*(1-xi)]
    ])

    # Jacobian J = D_N * coords.T
    J = D_N @ coords.T # shape (2, 2)
    detJ = np.linalg.det(J)
    invJ = np.linalg.inv(J)
    cjac = detJ * wt

    B = np.zeros((3, 8))
    for i in range(4):
        B[0, 2*i]   = invJ[0, 0]*D_N[0, i] + invJ[0, 1]*D_N[1, i]
        B[1, 2*i+1] = invJ[1, 0]*D_N[0, i] + invJ[1, 1]*D_N[1, i]
        B[2, 2*i]   = invJ[1, 0]*D_N[0, i] + invJ[1, 1]*D_N[1, i]
        B[2, 2*i+1] = invJ[0, 0]*D_N[0, i] + invJ[0, 1]*D_N[1, i]

    K_elem += cjac * (B.T @ D_ELAS @ B)

print("Element 4895 Stiffness matrix diag:\n", np.diag(K_elem))
print(f"Element area roughly: {cjac*4:.6e}")
