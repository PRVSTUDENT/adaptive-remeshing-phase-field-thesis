import os
import sys
import hashlib

base_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\206_f1713_new_mode1_adaptive_experiment"
sys.path.insert(0, base_dir)
import run_f1713_end_to_end_adaptive_pipeline as pipeline

phys_inp = os.path.join(base_dir, "PK_F1713_JOB2_ADAPTED_PHYS.inp")
prod_inp = os.path.join(base_dir, "PK_F1713_JOB2_ADAPTED_PROD.inp")

stats = pipeline.build_production_deck(phys_inp, prod_inp, job_name="PK_F1713_JOB2_ADAPTED")
print("Generated prod deck stats:", stats)

with open(prod_inp, "rb") as f:
    h = hashlib.sha256(f.read()).hexdigest()
print("New prod deck SHA-256:", h)
