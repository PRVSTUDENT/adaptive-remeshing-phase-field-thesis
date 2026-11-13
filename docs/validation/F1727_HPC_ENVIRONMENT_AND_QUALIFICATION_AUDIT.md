# F1727 HPC Environment and Technical Qualification Audit

**Protocol:** INDEPENDENT_STRUCTURED_REVIEW_V1  
**Task ID:** `F1727-METHOD-A-THREE-GEOMETRY-ADAPTIVE-MESH`  
**Correlation ID:** `HND-F1727-THREE-GEOMETRY-002`  
**Date:** 13 November 2026  
**Auditing Agent:** Gemini Antigravity (PRV_ADAPTIVE_REMESHING)  
**Governance & Policy:** Mandatory HPC-First Execution Policy & Guarded Non-Interactive SSH Protocol (`AGENTS.md`)  
**PBS Execution Gate:** `max_new_pbs_submissions = 0, consumed = 0` (Zero cluster jobs submitted)

---

## 1. Executive Summary

In compliance with the user-mandated **HPC-First Execution Policy** and Independent Review Finding **F1727-R02**, a comprehensive, non-interactive technical qualification audit of the high-performance computing (HPC) cluster environment was conducted.

The audit establishes that:
1. The remote cluster environment is fully accessible, healthy, and operational.
2. The authoritative Abaqus 2023 solver suite and Intel Fortran compiler (`ifx 2024.2.0`) are installed, licensed, and successfully loaded via environment modules.
3. The designated scratch directory `/scratch9/pr21vyci/runs` is accessible with valid read/write permissions.
4. The user queue state is clean with zero conflicting jobs running or queued.
5. All operations strictly conformed to the zero-submission stop condition (`max_new_pbs_submissions = 0, consumed = 0`).

---

## 2. Guarded SSH Execution & System Profile

All audit commands were executed non-interactively via the guarded wrapper:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "<cmd>"
```
under mandatory `-n -T -o BatchMode=yes` directives and 120-second timeout enforcement.

### System Host Profile
- **Login Node:** `mlogin01.cluster`
- **Operating System:** Linux `4.18.0-553.184.1.el8_10.x86_64` (Rocky / RHEL 8.10)
- **Architecture:** `x86_64` (64-bit GNU/Linux)
- **PBS Scheduler Server:** `mmaster`

---

## 3. Environment Modules and Software Stack

The software stack was audited via the cluster environment module system (`/etc/profile.d/modules.sh`):

### 3.1 Module Availability
- **Abaqus Modules Available:**
  - `abaqus/2021-incomplete`
  - `abaqus/2021`
  - `abaqus/2022`
  - `abaqus/2023` (Default Module `[D]`)
- **Compiler Modules Available:**
  - `intel/2024.2.0` (Intel oneAPI Compiler Suite)
  - `gcc/11.4.0` (GNU Compiler Collection baseline)

### 3.2 Loaded Module Verification
Executing `module load gcc/11.4.0 intel/2024.2.0 abaqus/2023` resolved the following authoritative toolchains:

1. **Abaqus 2023:**
   - Command Path: `/cluster/application/abaqus/2023/Commands/abaqus`
   - Release: Abaqus 2023 (Build 2022_09_28-20.11.55 183150)
   - Site ID: `200000000053187`
   - Verification Command: `abaqus information=release` (Completed Exit 0)
2. **Intel Fortran Compiler (`ifx`):**
   - Command Path: `/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin/ifx`
   - Version: `ifx (IFX) 2024.2.0 20240602`
   - Verification Command: `ifx --version` (Exit 0)

---

## 4. Scheduler Queues, Limits, and User Status

### 4.1 Queue Configuration (`qstat -q`)
The PBS server `mmaster` exposes the following active production queues:
- **`normal_imfdfkmq`:** Primary production queue for Mode-I fracture jobs.
  - Maximum Walltime: `336:00:00` (14 days)
  - State: Enabled and Running (`E R`)
- **`short_imfdfkmq`:** Rapid qualification and datacheck queue.
  - Maximum Walltime: `12:00:00`
  - State: Enabled and Running (`E R`)

### 4.2 User Running State (`qstat -u pr21vyci`)
- Active Running Jobs: `0`
- Queued Jobs: `0`
- Blocked / Held Jobs: `0`
- Conclusion: The scheduler queue is completely clear for upcoming authorized production runs.

---

## 5. Storage and Scratch Environment

The primary high-speed parallel scratch directory was audited:
- **Path:** `/scratch9/pr21vyci/runs`
- **Permissions:** `drwxr-xr-x` (Owner: `pr21vyci`, Group: `t2-dg-role_student`)
- **Status:** Operational and available for job staging.

---

## 6. Zero-Submission Compliance Statement

In strict adherence to the project governance rules (`AGENTS.md`) and the task boundary for `F1727`:
- **PBS Jobs Authorized:** `0`
- **PBS Jobs Submitted:** `0`
- **PBS Jobs Consumed:** `0`
- **Current Status:** `HPC_ENVIRONMENT_QUALIFIED_READY_FOR_GOVERNED_EXECUTION`

All Abaqus solver operations (coarse pre-analysis, adaptive remeshing, and forward fracture continuation) are fully prepared for execution on the HPC cluster upon explicit authorization in subsequent project phases.
