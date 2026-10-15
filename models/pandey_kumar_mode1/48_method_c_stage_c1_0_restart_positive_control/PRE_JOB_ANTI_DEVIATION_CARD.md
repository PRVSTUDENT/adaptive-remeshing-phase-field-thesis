# Pre-Job Anti-Deviation Card: Package 48 (Mode-I Native Restart Positive Control)

## 1. Proposal Task & Gate Alignment
- **Proposal Task:** Task 5 (Nonmatching State Transfer & Restart Workflow Qualification).
- **Active Gate:** Gate 6C (Mode-I State-Transfer Energy Preservation & Continuation).
- **Phase:** `MODE1_GATE6C_METHOD_C_STAGE_C1_0_RESTART_AUDIT`

## 2. Scientific Question & Hypothesis
- **Question:** Does native Abaqus `*RESTART, READ` preserve the coupled multi-layer phase-field and mechanical state in `f42_mixed_uel.for`, or does the separate OS process execution and `UEXTERNALDB(LOP=0/4)` architecture cause loss of `COMMON /CB_STATE_TRANS/`?
- **Hypothesis:** Native restart will restore element `SVARS` but will leave `COMMON /CB_STATE_TRANS/` un-populated because `f42_mixed_uel.for` lines 248–261 only ingest `SVARS` when `KSTEP == 1`, confirming why Package 47's 2-step re-equilibration architecture is necessary.

## 3. Single Intended Change
- Single change from baseline `M1_MB_INF_1S`: enable `*RESTART, WRITE, FREQUENCY=1, OVERLAY` in the donor run, and create a companion `*RESTART, READ, STEP=1` continuation deck.
- Frozen variables: Domain (1x1 mm), notch seam, material properties, phase-field parameters ($l_0 = 7.5\,\mu	ext{m}$, $G_c = 2.7	imes 10^{-3}\,	ext{kN/mm}$), production UEL (`CE8D5EDC...`).

## 4. Declared Acceptance Criteria
- [ ] Donor deck passes Abaqus 2023 datacheck with Exit 0.
- [ ] Recipient restart deck passes Abaqus 2023 datacheck with Exit 0.
- [ ] Experimental audit documents whether UEL SVARS and COMMON state are preserved.
