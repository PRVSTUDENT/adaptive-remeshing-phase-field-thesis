import numpy as np

def reconstruct_quad_element_force():
    # Far-field element coordinates (e.g. [0.4, 0.4] to [0.45, 0.45])
    # Coordinates of 4 nodes: (x1, y1), (x2, y2), (x3, y3), (x4, y4)
    x0, y0 = 0.40, 0.40
    dx, dy = 0.05, 0.05
    coords = np.array([
        [x0, y0],
        [x0 + dx, y0],
        [x0 + dx, y0 + dy],
        [x0, y0 + dy]
    ]) # 4x2
    
    # Material parameters
    E = 210.0 # kN/mm^2
    nu = 0.3
    k = 1.0e-7
    d = 0.0 # undamaged far field
    deg = (1.0 - d)**2 + k # = 1.0000001
    
    # Plane strain elasticity matrix
    c11 = E * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu)) * deg
    c12 = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu)) * deg
    c22 = c11
    c33 = E / (2.0 * (1.0 + nu)) * deg
    
    D_mat = np.array([
        [c11, c12, 0.0],
        [c12, c22, 0.0],
        [0.0, 0.0, c33]
    ])
    
    # Linear shear displacement field: u(x, y) = gamma * y, v(x, y) = 0
    # Top displacement at y=0.5 is 0.007585 -> gamma = 0.007585 / 1.0 = 0.007585
    gamma = 0.007585
    U = np.array([
        gamma * coords[0, 1], 0.0,
        gamma * coords[1, 1], 0.0,
        gamma * coords[2, 1], 0.0,
        gamma * coords[3, 1], 0.0
    ]) # 8x1
    
    # 2x2 Gauss quadrature
    xg = np.array([-1.0/np.sqrt(3), 1.0/np.sqrt(3), 1.0/np.sqrt(3), -1.0/np.sqrt(3)])
    yg = np.array([-1.0/np.sqrt(3), -1.0/np.sqrt(3), 1.0/np.sqrt(3), 1.0/np.sqrt(3)])
    w = np.array([1.0, 1.0, 1.0, 1.0])
    
    F_int = np.zeros(8)
    AMATRX = np.zeros((8, 8))
    
    for kpt in range(4):
        xi = xg[kpt]
        eta = yg[kpt]
        wt = w[kpt]
        
        # Shape function derivatives wrt natural coordinates
        dNdxi = 0.25 * np.array([-(1-eta), (1-eta), (1+eta), -(1+eta)])
        dNdeta = 0.25 * np.array([-(1-xi), -(1+xi), (1+xi), (1-xi)])
        
        # Jacobian
        J = np.zeros((2, 2))
        J[0, 0] = np.sum(dNdxi * coords[:, 0])
        J[0, 1] = np.sum(dNdxi * coords[:, 1])
        J[1, 0] = np.sum(dNdeta * coords[:, 0])
        J[1, 1] = np.sum(dNdeta * coords[:, 1])
        
        detJ = np.linalg.det(J)
        invJ = np.linalg.inv(J)
        cjac = detJ * wt
        
        # Global derivatives dN/dx, dN/dy
        dNdx = invJ[0, 0] * dNdxi + invJ[0, 1] * dNdeta
        dNdy = invJ[1, 0] * dNdxi + invJ[1, 1] * dNdeta
        
        # B matrix (3x8)
        B = np.zeros((3, 8))
        for i in range(4):
            B[0, 2*i]     = dNdx[i]
            B[1, 2*i + 1] = dNdy[i]
            B[2, 2*i]     = dNdy[i]
            B[2, 2*i + 1] = dNdx[i]
            
        strain = B @ U
        stress = D_mat @ strain
        
        F_int += cjac * (B.T @ stress)
        AMATRX += cjac * (B.T @ D_mat @ B)
        
    print("Element Force Reconstruction:")
    print("F_int:", F_int)
    print("AMATRX @ U:", AMATRX @ U)
    rel_err = np.linalg.norm(F_int - AMATRX @ U) / np.linalg.norm(F_int)
    print(f"Relative error between F_int and AMATRX @ U: {rel_err:.6e}")
    return rel_err

if __name__ == "__main__":
    reconstruct_quad_element_force()
