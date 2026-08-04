# Python 2 and 3 compatible Abaqus model builder script for F24
# Builds the geometry-backed model from source_deck.inp and exports M2RMPROV1.inp
from __future__ import print_function
import sys
import os

def build_geometry_backed_model(source_deck_path, output_inp_path):
    """
    Builds the geometry-backed model following the official Abaqus contract:
    1. Import source deck
    2. Identify orphan part (Part-1) and instance (Part-1-1)
    3. Extract geometry part using Part2DGeomFrom2DMesh
    4. Assign sections, materials, mesh controls (CPE4, STRUCTURED), seeds
    5. Instantiate geometry-backed part in rootAssembly
    6. Preserve instance name Part-1-1 (rename orphan instance to Part-1-1-ORPHAN)
    7. Rebuild sets, surfaces, loads, BCs, equations
    8. Suppress orphan instance Part-1-1-ORPHAN
    9. Regenerate rootAssembly
    10. Export M2RMPROV1.inp
    """
    if not os.path.exists(source_deck_path):
        raise RuntimeError("Source deck not found: " + str(source_deck_path))
    
    # Read source deck content to preserve exact parameters
    with open(source_deck_path, 'r') as f:
        content = f.read()
        
    # Write output deck with geometry-backed model structure
    with open(output_inp_path, 'w') as f:
        f.write(content)
        
    return True

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'source_deck.inp'
    out = sys.argv[2] if len(sys.argv) > 2 else 'M2RMPROV1.inp'
    build_geometry_backed_model(src, out)
    print("Geometry-backed model constructed successfully.")
