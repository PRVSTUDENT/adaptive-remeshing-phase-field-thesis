import os

src_inp = 'models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.inp'
with open(src_inp, 'r') as f:
    lines = f.readlines()

out_lines = []
out_lines.append('*HEADING\n')
out_lines.append('Task F1696 Method A Pandey-Kumar Section 4.3 Standard-Element Job-1\n')
out_lines.append('** Standard Abaqus Plane-Stress Quads (CPS4R) and Tris (CPS3)\n')
out_lines.append('** Dimensions: 65 x 120 mm, Notch: 10 x 0.4 mm, Holes: R=5, R=5, R=10\n')
out_lines.append('** Material: Linear Elastic E=210 GPa, nu=0.3\n')

# Copy nodes, elements, nsets, solid section, material, equations
in_header = True
in_step = False

for line in lines:
    if line.startswith('*HEADING') or in_header:
        if line.startswith('*NODE'):
            in_header = False
        else:
            continue
    if line.startswith('*STEP'):
        in_step = True
        break
    
    # Replace element types to plane stress
    if line.startswith('*ELEMENT, TYPE=CPE4'):
        line = '*ELEMENT, TYPE=CPS4R, ELSET=QUADS\n'
    elif line.startswith('*ELEMENT, TYPE=CPE3'):
        line = '*ELEMENT, TYPE=CPS3, ELSET=TRIS\n'
    elif line.startswith('*SOLID SECTION'):
        line = '*SOLID SECTION, ELSET=All_elem, MATERIAL=STEEL\n'
    
    out_lines.append(line)

# Add Step 1 and Step 2
step_block = """** ----------------------------------------------------------
** STEP 1: Linear Loading to u = 1.0 mm (2000 incs, delta_u = 5e-4 mm)
** ----------------------------------------------------------
*STEP, NAME=Step-1, NLGEOM=NO, INC=10000
*STATIC, DIRECT
0.0005, 1.0
*BOUNDARY
N_LOWER_HOLE, 1, 2, 0.0
N_UPPER_HOLE, 1, 1, 0.0
N_RP, 2, 2, 1.0
*OUTPUT, FIELD, FREQUENCY=20
*ELEMENT OUTPUT, ELSET=All_elem
MISESERI, MISESAVG, S, E, EVOL
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE PRINT, FREQ=20, NSET=N_RP
U2, RF2
*END STEP
** ----------------------------------------------------------
** STEP 2: Loading to u = 1.5 mm (2500 incs, delta_u = 2e-4 mm)
** ----------------------------------------------------------
*STEP, NAME=Step-2, NLGEOM=NO, INC=25000
*STATIC, DIRECT
0.0002, 0.5
*BOUNDARY
N_RP, 2, 2, 1.5
*OUTPUT, FIELD, FREQUENCY=20
*ELEMENT OUTPUT, ELSET=All_elem
MISESERI, MISESAVG, S, E, EVOL
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE PRINT, FREQ=20, NSET=N_RP
U2, RF2
*END STEP
"""

out_lines.append(step_block)

target_inp = 'models/pandey_kumar_mode1/196_pk_sec43_standard_element_job1/PK_SEC43_STANDARD_JOB1.inp'
with open(target_inp, 'w') as f:
    f.writelines(out_lines)

print(f'Successfully wrote {target_inp}')
