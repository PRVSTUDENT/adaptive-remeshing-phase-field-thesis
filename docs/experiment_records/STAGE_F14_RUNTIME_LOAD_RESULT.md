# Stage F14 runtime-load result

Job `1381368.mmaster02` completed on `mnode106/0` with PBS and Abaqus return
codes zero, walltime 18 seconds, and peak recorded memory 190,488 kB.

Source SHA-256 is
`082f5f182c1083990363e12b9fa69557133c0e08a94bd7db465d68f401f6eb53`;
deck SHA-256 is
`b2827e6078a1fae0b8179adfc31dc079cea1e1e39c7c6cbbd678167658b686fe`.
The repair removed `GET_ENVIRONMENT_VARIABLE` and used documented
`GETOUTDIR(OUTDIR,LENOUTDIR)` and `GETJOBNAME(JOBNAME,LENJOBNAME)` calls.

The persistent-library symbol audit contains `getoutdir_` and `getjobname_`
but no `for_getenv_err`. Abaqus loaded the user library, began step 1 / increment
1, entered UEL element 1 integration point 1, created
`M2RTLOAD1_uel_entry.log` in the PBS output directory, and retained the file
after scratch cleanup. The single increment reached time 0.1 and the STA file
reports successful completion. No COMMON bounds marker occurred.

Classification: `abaqus_user_library_runtime_contract_qualified`. This permits
preparation only, not submission, of a future rollback pair.
