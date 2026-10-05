#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_shared_memory_8thread_template_and_guards.py
-------------------------------------------------------
Unit regression test suite enforcing:
1. 8-Thread PBS execution template directives and SMP single-node constraints.
2. Storage compliance guards (Exit 88) and multi-node MPI rejection guards (Exit 89).
3. Exact Abaqus CLI launch syntax (cpus=8, mp_mode=threads, double=both, interactive).
4. Guarded submission wrapper integrity and notification integration.
5. commands.txt synchronization documenting serial reference and 8-thread modes.
6. Mathematical and empirical consistency of speedup S_8 and parallel efficiency eta_8.
7. Active Gate-6B 5-job serial provenance justification.
8. REGRESSION GUARDS:
   a. Guard against MPI race-condition misnomer (must identify separate address space / unsynchronized state).
   b. Guard against generic/unqualified thread-safety claims (must require empirical scope constraint).
   c. Guard against treating 16-thread execution as qualified without Stage-A/B proof.
   d. Guard against treating Exit status alone as parallel qualification.
   e. Guard against removal of serial authoritative reference requirement.
   f. Guard enforcing explicit 6-point provenance warning for future modifications.
"""

import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PBS_TEMPLATE_PATH = os.path.join(REPO_ROOT, "scripts", "hpc", "templates", "submit_mode1_8thread_scratch_template.pbs")
SH_TEMPLATE_PATH = os.path.join(REPO_ROOT, "scripts", "hpc", "templates", "submit_mode1_8thread_scratch_template.sh")
COMMANDS_TXT_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "commands.txt")
AUDIT_DOC_PATH = os.path.join(REPO_ROOT, "docs", "methods", "MODE1_SHARED_MEMORY_8THREAD_PARITY_AND_SCALING_AUDIT.md")


def test_8thread_pbs_template_directives():
    """Verify that the 8-thread PBS template contains required PBS directives."""
    assert os.path.isfile(PBS_TEMPLATE_PATH), f"Missing PBS template: {PBS_TEMPLATE_PATH}"
    with open(PBS_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Core PBS Directives
    assert re.search(r"#PBS\s+-l\s+(nodes=1:ppn=8|select=1:ncpus=8)", content), "Must enforce single-node 8-CPU allocation"
    assert "#PBS -q normal_imfdfkmq" in content, "Must target normal_imfdfkmq production queue"
    assert re.search(r"#PBS\s+-l\s+mem=16gb", content), "Must allocate 16GB memory"
    assert "#PBS -m abe" in content, "Must include PBS mail directives"
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content, "Must target valid Freiberg email"


def test_8thread_storage_and_mpi_guards():
    """Verify that the 8-thread PBS template enforces Exit 88 storage and Exit 89 MPI guards."""
    with open(PBS_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Storage Guard
    assert "exit 88" in content, "Must contain Exit 88 storage guard"
    assert "/home/" in content, "Must check for prohibited /home/ execution"

    # MPI / Multi-Node Rejection Guard
    assert "exit 89" in content, "Must contain Exit 89 MPI/multi-node rejection guard"
    assert "PBS_NODEFILE" in content, "Must inspect PBS_NODEFILE to detect multi-node allocation"

    # Notification integration
    assert "source ./job_notifications.sh" in content, "Must source job_notifications.sh"
    assert "notification_install_terminal_trap" in content, "Must install terminal notification trap"
    assert "notify_start" in content, "Must issue notify_start"


def test_8thread_abaqus_cli_invocation():
    """Verify that the Abaqus launch command uses threads mode and interactive execution."""
    with open(PBS_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify mp_mode=threads
    assert 'mp_mode="threads"' in content or 'mp_mode=threads' in content or 'MP_MODE="threads"' in content, "Must specify mp_mode=threads"
    assert "mp_mode=mpi" not in content, "Must never specify mp_mode=mpi"
    assert "interactive" in content, "Must execute in interactive mode to retain stdout/stderr"
    assert "double=both" in content, "Must enforce double precision"
    assert "f42_mixed_uel.for" in content, "Must reference f42_mixed_uel.for user subroutine"


def test_8thread_submission_wrapper():
    """Verify that the submission wrapper enforces scratch execution and checks dependencies."""
    assert os.path.isfile(SH_TEMPLATE_PATH), f"Missing submission wrapper: {SH_TEMPLATE_PATH}"
    with open(SH_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "exit 88" in content, "Wrapper must enforce Exit 88 for /home/ launches"
    assert "f42_mixed_uel.for" in content, "Wrapper must verify user subroutine presence"
    assert "qsub" in content, "Wrapper must invoke qsub"
    assert "notify_submitted" in content, "Wrapper must issue Telegram submission notification"


def test_commands_txt_documentation():
    """Verify that commands.txt documents both serial baseline and 8-thread accelerated modes."""
    assert os.path.isfile(COMMANDS_TXT_PATH), f"Missing commands.txt: {COMMANDS_TXT_PATH}"
    with open(COMMANDS_TXT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SECTION 1: CANONICAL SERIAL REFERENCE BASELINE" in content
    assert "SECTION 2: EMPIRICALLY QUALIFIED 8-THREAD SHARED-MEMORY" in content
    assert "SECTION 3: FAST HEADLESS POST-PROCESSING" in content
    assert "SECTION 4: MULTI-RANK MPI DISQUALIFICATION" in content
    assert "cpus=8 mp_mode=threads" in content
    assert "Speedup S_8 = 3.62x" in content


def test_8thread_audit_document_consistency():
    """Verify that the methods audit document records exact metrics and governance justifications."""
    assert os.path.isfile(AUDIT_DOC_PATH), f"Missing audit doc: {AUDIT_DOC_PATH}"
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Metric assertions
    assert "17,609" in content or "17{,}609" in content, "Must record serial walltime 17,609 s"
    assert "4,862" in content or "4{,}862" in content, "Must record 8T Stage-A walltime 4,862 s"
    assert "3.62" in content, "Must record speedup 3.62x"
    assert "45.3" in content and "45.0" in content, "Must record parallel efficiency percentages"
    assert "137.909558" in content, "Must record exact K0 match"
    assert "0.74370082" in content, "Must record exact F_max match"
    assert "0.005733" in content, "Must record exact peak displacement match"

    # Governance & Rationale assertions
    assert "1410179" in content and "1410180" in content and "1410357" in content
    assert "STAGE A: CROSS-THREAD PARITY" in content or "Stage A" in content
    assert "STAGE B: ALLOCATION REPEAT DETERMINISM" in content or "Stage B" in content
    assert "COMMON /CB_STATE_TRANS/" in content, "Must explain Fortran COMMON block mechanism"


def test_governed_speedup_math_invariants():
    """Programmatically verify the mathematical speedup and efficiency values."""
    t1 = 17609.0
    t4 = 7627.0
    t8_a = 4862.0
    t8_b = 4895.0

    s4 = t1 / t4
    eta4 = (s4 / 4.0) * 100.0

    s8_a = t1 / t8_a
    eta8_a = (s8_a / 8.0) * 100.0

    s8_b = t1 / t8_b
    eta8_b = (s8_b / 8.0) * 100.0

    assert round(s4, 2) == 2.31
    assert round(eta4, 1) == 57.7 or round(eta4, 1) == 57.8

    assert round(s8_a, 2) == 3.62
    assert round(eta8_a, 1) == 45.3

    assert round(s8_b, 2) == 3.60
    assert round(eta8_b, 1) == 45.0


def test_guard_against_mpi_race_condition_misnomer():
    """Regression Guard: Ensure MPI failure is not called a 'race condition across MPI ranks'."""
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        audit_content = f.read()
    with open(COMMANDS_TXT_PATH, "r", encoding="utf-8") as f:
        commands_content = f.read()

    # Disallow "race conditions across ranks" or "race condition across MPI ranks"
    for text in [audit_content, commands_content]:
        assert not re.search(r"race\s+conditions?\s+across\s+(?:MPI\s+)?ranks", text, re.IGNORECASE), \
            "Must not describe MPI rank-local state desynchronization as a shared-memory race condition"

    # Require accurate mechanism description
    assert "isolated process address spaces" in audit_content or "separate address spaces" in audit_content or "rank-local" in audit_content
    assert "TRUE_MULTIRANK_MPI_NOT_QUALIFIED" in audit_content


def test_guard_against_generic_thread_safety_claim():
    """Regression Guard: Ensure documentation scopes thread safety to the tested Mode-I configuration."""
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        audit_content = f.read()

    # Disallow positive generic global thread-safety assertions
    assert not re.search(r"is\s+(?:generically|universally)\s+thread-safe", audit_content, re.IGNORECASE), \
        "Must not claim the UEL is generically or universally thread-safe"
    assert "PROVEN 100% thread-safe" not in audit_content, "Must not claim unqualified 100% thread safety"
    assert "8THREAD_SHARED_MEMORY_EXECUTION_EMPIRICALLY_QUALIFIED_FOR_THE_TESTED_MODE1_FORMULATION_AND_CONTROLS" in audit_content


def test_guard_against_unqualified_16thread_claim():
    """Regression Guard: Ensure 16 threads are treated as unqualified until Stage-A and Stage-B pass."""
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        audit_content = f.read()

    assert re.search(r"16[- ]threads?\s+execution\s+remains\s+(?:\*\*|`|)unqualified", audit_content, re.IGNORECASE) or \
           re.search(r"16[- ]threads?.*?unqualified", audit_content, re.IGNORECASE), \
           "Must explicitly state that 16 threads remain unqualified without Stage-A/B proof"


def test_guard_against_exit_status_alone_as_qualification():
    """Regression Guard: Ensure Exit status 0 alone is rejected as parallel qualification."""
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        audit_content = f.read()

    assert "Exit_status=0" in audit_content or "Exit status 0" in audit_content or "Exit 0" in audit_content
    assert "insufficient" in audit_content.lower()


def test_guard_against_removal_of_serial_authoritative_reference():
    """Regression Guard: Ensure 1-CPU serial reference standard is mandatory."""
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        audit_content = f.read()
    with open(COMMANDS_TXT_PATH, "r", encoding="utf-8") as f:
        commands_content = f.read()

    assert "authoritative reference standard" in audit_content.lower() or "authoritative reference" in audit_content.lower()
    assert "MANDATORY authoritative reference" in commands_content or "authoritative reference" in commands_content.lower()


def test_guard_provenance_invalidation_warning():
    """Regression Guard: Ensure the 6-point provenance invalidation warning is preserved."""
    with open(AUDIT_DOC_PATH, "r", encoding="utf-8") as f:
        audit_content = f.read()

    assert "Provenance Invalidation Boundary" in audit_content or "Provenance & Code-Modification Warning" in audit_content
    assert "f42_mixed_uel.for" in audit_content
    assert "COMMON /CB_STATE_TRANS/" in audit_content
    assert "call ordering" in audit_content
    assert "compiler" in audit_content.lower()
    assert "thread count" in audit_content.lower()
