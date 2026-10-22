"""
Build Package 86 Same-Process Staggered Control Input Deck.
Takes the authentic Package 76 model definition (mesh, UEL, equations, boundary)
and appends a 4-step sequence without restart:
Step 1: DONOR_LOADING (monotonic up to target u_top = 0.00254010735 mm at t = 0.50802148)
Step 2: PHASE_SUBPROBLEM (Hold converged mechanical field, evaluate damage subproblem)
Step 3: MECHANICAL_SUBPROBLEM (Hold damage field, relax mechanical DOFs)
Step 4: COUPLED_CHECK (Release artificial interior constraints, evaluate coupled equilibrium)
"""
import os
import hashlib

def main():
    donor_inp_path = r"models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/candidate_donor_h0025_visual.inp"
    pkg86_dir = r"models/pandey_kumar_mode1/86_donor_sameprocess_staggered_control"
    os.makedirs(pkg86_dir, exist_ok=True)
    out_inp_path = os.path.join(pkg86_dir, "M1_DONOR_SAMEPROCESS_STAGGERED.inp")
    
    with open(donor_inp_path, "r") as f:
        lines = f.readlines()
        
    # Find where Step 1 starts
    step_start_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith("*step"):
            step_start_idx = idx
            break
            
    assert step_start_idx > 0, "Could not find *Step in donor inp"
    
    model_lines = lines[:step_start_idx]
    
    # We need to add N_ALL_PHYSICAL and N_INTERIOR_AND_BOTTOM before *Step
    # Check if N_ALL_PHYSICAL is already in model_lines
    additional_nsets = [
        "** ==========================================================\n",
        "** ADDITIONAL NODE SETS FOR STAGGERED SUBPROBLEMS\n",
        "** ==========================================================\n",
        "*Nset, nset=N_ALL_PHYSICAL, generate\n",
        "1, 1698, 1\n",
        "*Nset, nset=N_INTERIOR_AND_BOTTOM, generate\n",
        "1, 1640, 1\n",
        "1682, 1698, 1\n"
    ]
    
    # Define the 4 steps
    steps_content = """** ==========================================================
** STEP 1: DONOR_LOADING
** Monotonic loading to target checkpoint u_top = 0.00254010735 mm
** ==========================================================
*Step, name=DONOR_LOADING, nlgeom=NO, inc=2000
*Static
1.0e-3, 0.50802148, 1.0e-8, 5.0e-3
*Boundary
N_RP, 2, 2, 0.00254010735
N_RP, 1, 1, 0.0
** Output requests
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV, S, E
*Output, history, frequency=1
*Node Output, nset=N_RP
U2, RF2
*Energy Output
ALLSE, ALLWK, ALLFD, ALLIE
*End Step
** ==========================================================
** STEP 2: PHASE_SUBPROBLEM
** Hold converged mechanical field, evaluate damage subproblem
** ==========================================================
*Step, name=PHASE_SUBPROBLEM, nlgeom=NO, inc=100
*Static
1.0, 1.0, 1e-12, 1.0
*Boundary, fixed
N_ALL_PHYSICAL, 1, 1
N_INTERIOR_AND_BOTTOM, 2, 2
*Boundary
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_RP, 2, 2, 0.00254010735
N_RP, 1, 1, 0.0
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV, S, E
*Output, history, frequency=1
*Node Output, nset=N_RP
U2, RF2
*Energy Output
ALLSE, ALLWK, ALLFD, ALLIE
*End Step
** ==========================================================
** STEP 3: MECHANICAL_SUBPROBLEM
** Hold updated damage field, relax mechanical DOFs
** ==========================================================
*Step, name=MECHANICAL_SUBPROBLEM, nlgeom=NO, inc=100
*Static
1.0, 1.0, 1e-12, 1.0
*Boundary, op=NEW, fixed
N_ALL_PHYSICAL, 3, 3
*Boundary
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_RP, 2, 2, 0.00254010735
N_RP, 1, 1, 0.0
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV, S, E
*Output, history, frequency=1
*Node Output, nset=N_RP
U2, RF2
*Energy Output
ALLSE, ALLWK, ALLFD, ALLIE
*End Step
** ==========================================================
** STEP 4: COUPLED_CHECK
** Release artificial interior constraints, evaluate physical equilibrium
** ==========================================================
*Step, name=COUPLED_CHECK, nlgeom=NO, inc=100
*Static
1.0, 1.0, 1e-12, 1.0
*Boundary, op=NEW
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_RP, 2, 2, 0.00254010735
N_RP, 1, 1, 0.0
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=umatelem
SDV, S, E
*Output, history, frequency=1
*Node Output, nset=N_RP
U2, RF2
*Energy Output
ALLSE, ALLWK, ALLFD, ALLIE
*End Step
"""
    
    with open(out_inp_path, "w", newline="\n") as f:
        f.writelines(model_lines)
        f.writelines(additional_nsets)
        f.write(steps_content)
        
    with open(out_inp_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest().upper()
        
    print(f"Generated {out_inp_path}")
    print(f"SHA256: {digest}")
    print(f"Total lines: {len(model_lines) + len(additional_nsets) + len(steps_content.splitlines())}")

if __name__ == "__main__":
    main()
