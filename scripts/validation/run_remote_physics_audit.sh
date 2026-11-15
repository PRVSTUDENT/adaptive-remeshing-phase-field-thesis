#!/bin/bash
set -e
module load abaqus/2023 || true
cd /scratch9/pr21vyci/runs/mode1_pk_f1776_fracture_batch
abaqus python /scratch9/pr21vyci/runs/mode1_pk_f1776_fracture_batch/audit_case5_physics.py
