#!/usr/bin/env python3
"""
Simulate exact UEL call for JTYPE=2 Element 9877 with coordinates from M2STATE_FRACFIX_RESTART2R5.inp (pure Python).
"""
from pathlib import Path

def simulate_elem_9877():
    root = Path(__file__).resolve().parent.parent.parent
    inp_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp"
    
    nodes = {}
    with open(inp_path, "r", errors="ignore") as f:
        in_node = False
        for line in f:
            if line.startswith("*NODE"):
                in_node = True
                continue
            elif in_node and line.startswith("*"):
                in_node = False
            elif in_node:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    
    enodes = [1, 2, 122, 121]
    coords = [[0.0]*4 for _ in range(2)]
    for i, nid in enumerate(enodes):
        coords[0][i] = nodes[nid][0]
        coords[1][i] = nodes[nid][1]
        print("Node %d (ID %d): X=%.6f, Y=%.6f" % (i+1, nid, coords[0][i], coords[1][i]))
        
    ONE = 1.0
    TWO = 2.0
    FOUR = 4.0
    HALF = 0.5
    ZERO = 0.0
    
    E_MOD = 210.0
    E_NU = 0.3
    E_K = 1.0e-7
    D_VAL = 0.0
    
    DEG = (ONE - D_VAL)**2 + E_K
    C11 = E_MOD*(ONE-E_NU)/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
    C12 = E_MOD*E_NU/((ONE+E_NU)*(ONE-TWO*E_NU)) * DEG
    C22 = C11
    C33 = E_MOD/(TWO*(ONE+E_NU)) * DEG
    
    print("C11=%f, C12=%f, C33=%f" % (C11, C12, C33))
    
    XG4 = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
    YG4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]
    W4 = [1.0, 1.0, 1.0, 1.0]
    
    for test_u_name, U in [("Zero U", [0.0]*8), ("Arbitrary U", [0.0, 0.0, 0.0, 0.0, 1e-4, 1e-4, 1e-4, 1e-4])]:
        print("\n--- Testing with %s ---" % test_u_name)
        F_INT = [0.0]*8
        RHS = [0.0]*8
        AMATRX = [[0.0]*8 for _ in range(8)]
        
        for kpt in range(4):
            xi = XG4[kpt]
            eta = YG4[kpt]
            wt = W4[kpt]
            
            d_n = [[0.0]*4 for _ in range(2)]
            d_n[0][0] = -0.25*(ONE-eta)
            d_n[0][1] =  0.25*(ONE-eta)
            d_n[0][2] =  0.25*(ONE+eta)
            d_n[0][3] = -0.25*(ONE+eta)
            d_n[1][0] = -0.25*(ONE-xi)
            d_n[1][1] = -0.25*(ONE+xi)
            d_n[1][2] =  0.25*(ONE+xi)
            d_n[1][3] =  0.25*(ONE-xi)
            
            detJ = ((coords[0][1]-coords[0][0])*(coords[1][3]-coords[1][0]) -
                    (coords[0][3]-coords[0][0])*(coords[1][1]-coords[1][0])) / FOUR
            if detJ <= ZERO:
                detJ = 1.0e-6
            cjac = detJ * wt
            
            invJ = [[0.0]*2 for _ in range(2)]
            invJ[0][0] =  (coords[1][3]-coords[1][0])/(FOUR*detJ)
            invJ[0][1] = -(coords[1][1]-coords[1][0])/(FOUR*detJ)
            invJ[1][0] = -(coords[0][3]-coords[0][0])/(FOUR*detJ)
            invJ[1][1] =  (coords[0][1]-coords[0][0])/(FOUR*detJ)
            
            B = [[0.0]*8 for _ in range(3)]
            for i in range(4):
                B[0][2*i]   = invJ[0][0]*d_n[0][i] + invJ[0][1]*d_n[1][i]
                B[0][2*i+1] = ZERO
                B[1][2*i]   = ZERO
                B[1][2*i+1] = invJ[1][0]*d_n[0][i] + invJ[1][1]*d_n[1][i]
                B[2][2*i]   = B[1][2*i+1]
                B[2][2*i+1] = B[0][2*i]
                
            strain = [0.0]*3
            for i in range(8):
                strain[0] += B[0][i]*U[i]
                strain[1] += B[1][i]*U[i]
                strain[2] += B[2][i]*U[i]
                
            stress = [0.0]*3
            stress[0] = C11*strain[0] + C12*strain[1]
            stress[1] = C12*strain[0] + C22*strain[1]
            stress[2] = C33*strain[2]
            
            for i in range(8):
                f_val = cjac*(B[0][i]*stress[0] + B[1][i]*stress[1] + B[2][i]*stress[2])
                F_INT[i] += f_val
                RHS[i] -= f_val
                
            for i in range(8):
                for j in range(8):
                    AMATRX[i][j] += cjac*(
                        B[0][i]*(C11*B[0][j] + C12*B[1][j]) +
                        B[1][i]*(C12*B[0][j] + C22*B[1][j]) +
                        B[2][i]*(C33*B[2][j])
                    )
                    
        print("detJ = %e" % detJ)
        print("F_INT = %s" % [round(x, 8) for x in F_INT])
        print("RHS = %s" % [round(x, 8) for x in RHS])
        print("AMATRX diag = %s" % [round(AMATRX[i][i], 4) for i in range(8)])

if __name__ == "__main__":
    simulate_elem_9877()
