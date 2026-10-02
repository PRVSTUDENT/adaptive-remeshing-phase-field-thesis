#!/usr/bin/env python3
"""
Test valid structured triangle generation without wrapping.
"""
from typing import Dict, List, Tuple
import math

def area_tri(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> float:
    return 0.5 * ((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p3[0] - p1[0]) * (p2[1] - p1[1]))

def test_mesh_generation():
    nx = 120
    ny = 84
    dx = 1.0 / (nx - 1)
    dy = 1.0 / (ny - 1)

    all_grid_nodes = {}
    for i in range(ny):
        for j in range(nx):
            nid = i * nx + j + 1
            x = -0.5 + j * dx
            y = -0.5 + i * dy
            all_grid_nodes[nid] = (round(x, 6), round(y, 6))

    eid = 1
    quads = {}
    for i in range(ny - 1):
        for j in range(nx - 1):
            if eid > 9600:
                break
            n1 = i * nx + j + 1
            n2 = i * nx + j + 2
            n3 = (i + 1) * nx + j + 2
            n4 = (i + 1) * nx + j + 1
            quads[eid] = [n1, n2, n3, n4]
            eid += 1
        if eid > 9600:
            break

    tris = {}
    # 276 triangles generated properly using cell indexing (i, j) with 0 <= j < nx - 1
    num_cols = nx - 1  # 119 cells per row
    for k in range(276):
        i = k // num_cols
        j = k % num_cols
        n1 = i * nx + j + 1
        n2 = i * nx + j + 2
        n3 = (i + 1) * nx + j + 1
        
        a = area_tri(all_grid_nodes[n1], all_grid_nodes[n2], all_grid_nodes[n3])
        if a <= 0:
            n2, n3 = n3, n2
        tris[eid] = [n1, n2, n3]
        eid += 1

    print(f"Generated {len(quads)} quads, {len(tris)} tris (total {len(quads)+len(tris)})")

    # Check X spans and edge lengths of all tris
    max_span_x = 0.0
    min_detJ = 1e9
    for tid, enodes in tris.items():
        coords = [all_grid_nodes[nid] for nid in enodes]
        xs = [c[0] for c in coords]
        span_x = max(xs) - min(xs)
        if span_x > max_span_x:
            max_span_x = span_x
        detJ = (coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1]) - (coords[2][0]-coords[0][0])*(coords[1][1]-coords[0][1])
        if detJ < min_detJ:
            min_detJ = detJ

    print(f"Max triangle X-span: {max_span_x:.6f} mm (must be <= {dx:.6f})")
    print(f"Min triangle detJ: {min_detJ:.6e} (must be > 0)")
    assert max_span_x <= dx + 1e-5, f"Span {max_span_x} exceeds dx {dx}"
    assert min_detJ > 0, f"Min detJ {min_detJ} <= 0"
    print("ALL MESH TOPOLOGY CHECKS PASSED!")

if __name__ == "__main__":
    test_mesh_generation()
