# rescue_bridge_request.py
# Reconstructs and writes bridge_request.ready for HND-b0c972db9bcd

import os
import shutil

CONTROLLER_PATH = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"
BRIDGE_DIR = r"C:\Users\pruth\OpenClawPAD\ChatGPTBridge"
RULES_PATH = os.path.join(BRIDGE_DIR, "bridge_rules.txt")
REQUEST_TMP = os.path.join(BRIDGE_DIR, "bridge_request.tmp")
REQUEST_READY = os.path.join(BRIDGE_DIR, "bridge_request.ready")
ARCHIVE_DIR = os.path.join(BRIDGE_DIR, "archive")

def rescue_request():
    with open(CONTROLLER_PATH, "r", encoding="utf-8") as f:
        loop = f.read()

    # Extract ProjectAlignmentGuard
    guard_start_marker = '$ProjectAlignmentGuard = @"\n'
    guard_start = loop.find(guard_start_marker)
    if guard_start == -1:
        # try CRLF
        guard_start_marker = '$ProjectAlignmentGuard = @"\r\n'
        guard_start = loop.find(guard_start_marker)
    
    guard_start += len(guard_start_marker)
    guard_end = loop.find('"@\r\n\r\nfunction', guard_start)
    if guard_end == -1:
        guard_end = loop.find('"@\n\nfunction', guard_start)
    
    guard = loop[guard_start:guard_end].strip()

    with open(RULES_PATH, "r", encoding="utf-8") as f:
        rules = f.read().strip()

    agent_resp = "I will wait for the search task to complete."
    quota_text = "Quota check was not scheduled for this turn."
    handoff_id = "HND-b0c972db9bcd"

    prompt_body = f"""[BRIDGE_HANDOFF_ID={handoff_id}]

AUTOMATED ANTIGRAVITY WORKFLOW TURN

HUMAN (USER) & SUPERVISOR DIRECTIVE STATUS:
The supervisor and human user have explicitly directed:
1. Temporarily narrow the thesis work to the basic Pandey-Kumar Mode-I benchmark ONLY ("We need to have understood everything related to the first model before we increase complexity").
2. Mode-II and multi-step state transfer continuation are PAUSED/ARCHIVED and must NOT drive active instructions.
3. Guide Antigravity according to the supervisor's preferred scientific logic:
   Define problem -> Define expected solution -> Establish reference -> Apply adaptive method -> Compare -> Explain discrepancies.
4. Require defensible scientific rigor: distinguish "I know this", "I verified this numerically", and "I do not yet understand this".
5. Target deliverables: condensed 5-chapter Mode-I report, exact multi-quantity convergence comparisons (F-u curve, peak force, displacement at peak, UEL energy limitation, phase-field distribution, crack path, computational cost), and clean reproduction package (.inp, .for, .py, commands.txt).
6. NEW HUMAN DIRECTIVE (2026-09-10): the verified supervisor handoff package is a baseline snapshot, NOT the end of Mode-I research. Continue working to resolve (A) the 71,320-element stiffness/response anomaly and (B) the 71,320-vs-~13,941 Pandey-Kumar native-remesh discrepancy.
7. Priority A comes first for solver/debugging work. Do not advance Gate 7, Mode-II, or state transfer merely because Gates 0-6 were packaged.

---------------- PROJECT / THESIS ALIGNMENT GUARD ----------------
{guard}
-------------- END PROJECT / THESIS ALIGNMENT GUARD --------------

The following is the latest response from Antigravity:

---------------- ANTIGRAVITY RESPONSE ----------------
{agent_resp}
-------------- END ANTIGRAVITY RESPONSE --------------

---------------- QUOTA GUARD SNAPSHOT ----------------
{quota_text}
-------------- END QUOTA GUARD SNAPSHOT --------------

Determine the next instruction to send to Antigravity.

Workflow requirements:
1. Give only the next actionable instruction. Do not add unnecessary commentary.
2. The human user has fully authorized today's project tasks and PBS submissions. Once candidate validation and datacheck pass, immediately authorize Antigravity to submit the validated PBS job.
3. If a PBS job has been submitted, preserve the exact job ID.
4. When asking Antigravity to perform work, require it to write "Finished" at the end.
5. Return only the next instruction that should be sent to Antigravity.
6. Concurrency & Batch Rules (Holiday-Window Concurrency Policy Floor >= 10, Up to 15-20 Useful Mode-I Jobs):
- The cluster queue normal_imfdfkmq operates under the Holiday-Window Concurrency Policy with demonstrated capacity >= 10 concurrent jobs (up to 640 CPUs / 4 TB RAM).
- Active running jobs (R or Q) do NOT block independent, scientifically justified Mode-I tasks, offline analysis, evidence evaluations, post-processing, or submission of independent companion/repeat/scaling jobs.
- Do NOT reply "stop" if:
  (a) Free cluster CPU capacity remains under the 640 CPU limit, AND
  (b) There is independent, scientifically justified Mode-I work ready to perform (such as submitting independent thread-determinism repeats, evaluating newly terminal jobs, offline reconciliation audits, or preparing/submitting the next batch), AND
  (c) The running jobs are independent and do not block that work.
  In this case, instruct Antigravity to proceed with that independent work!
- Reply "stop" ONLY if:
  All authorized and scientifically justified independent Mode-I work is already executing or completed, and the workflow is genuinely blocked waiting on running jobs to reach terminal state before any further scientific progress can be made.
- CURRENT MODE-I FUNDAMENTALS GOVERNANCE (POST-17-SEPTEMBER-2026 MEETING):
  ModeIReproductionStatus is CLOSED_WITH_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION.
  Mechanical N_BOTTOM defect is RESOLVED_AND_CLOSED.
  Active phase: MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE.
  Priority 1 is UEL Energy Formulation and Output Audit (offline derivation, source audit, energy balance formulation, non-invasive code design, report updates).
  ModeIFundamentalsActionable is TRUE.
  With zero Q/R jobs, independent fundamentals work (energy audit, weak form derivations, report updating) is ACTIONABLE. Do NOT reply "stop" merely because zero jobs are in the queue.
- The exact meaning of "stop":
  "stop" means: leave the currently running PBS jobs untouched; no further independent action is possible right now.
  It does NOT mean: "stop using the cluster" or "halt research while independent work or free HPC capacity remains."

7. When a fresh scheduler result is provided after that wait, evaluate that result and decide the next action.

8. If the scheduler result is terminal (F/C/E), do NOT reply "stop" merely because the job finished. Give the next concrete instruction required to retrieve, inspect, diagnose, or evaluate the actual job evidence.

9. Do not choose the scheduler polling interval yourself.

10. If the supplied information is insufficient for a safe next instruction, reply exactly:
ESCALATION_UNRESOLVED"""

    assembled = f"""{prompt_body}

---------------- BRIDGE CONTROLLER RULES ----------------
{rules}
---------------- END BRIDGE CONTROLLER RULES ----------------

Determine the next instruction to send to Antigravity."""

    print(f"Reconstructed assembled prompt length: {len(assembled)} characters")

    # Save to archive permanently first!
    arch_file = os.path.join(ARCHIVE_DIR, f"request_{handoff_id}.txt")
    with open(arch_file, "w", encoding="utf-8") as f:
        f.write(assembled)
    print(f"Saved archive: {arch_file}")

    # Atomically write to bridge_request.ready
    with open(REQUEST_TMP, "w", encoding="utf-8") as f:
        f.write(assembled)
    
    shutil.move(REQUEST_TMP, REQUEST_READY)
    print(f"SUCCESS: Recreated atomic request at {REQUEST_READY}")

if __name__ == "__main__":
    rescue_request()
