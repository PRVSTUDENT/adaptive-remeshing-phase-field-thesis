# F5 SSH transport recovery preflight

Date: 2026-07-30  
Agent: Codex  
Starting commit: `37182b40710d0106dde220271174ef7869ad0c5c`

The dedicated Windows SSH configuration exists. Sanitized resolution showed
that `tu_freiberg` selects remote user `pr21vyci`, `IdentitiesOnly=yes` and an
existing dedicated identity, whereas the direct hostname selected `pruth`,
`IdentitiesOnly=no` and no existing default identity. The SSH-agent service is
stopped/disabled, but the configured identity connected without it.

The alias connected to `mlogin01.cluster`; `qstat -u pr21vyci` was accessible
and empty. Candidate modules are visible. Both read-only order inspections
preserved:

- ifort 2021.13.0 at the Intel 2024.2 compiler path
- ifx 2024.2.0 at the Intel 2024.2 compiler path
- Abaqus 2023 at `/cluster/application/abaqus/2023/Commands/abaqus`

Order A (`gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`) remains selected
because it matches prior successful UEL evidence. Environment presence checks
for `LD_LIBRARY_PATH`, `LIBRARY_PATH` and `CPATH` passed.

No verbose diagnostic was needed because the alias succeeded. No key contents
or verbose sensitive logs were captured. No authorization was activated and
qsub, compilation, datacheck and solver counts are all zero.

Classification:
`stage_f5_ssh_transport_recovered_compiler_environment_readonly_preflight_pass`.
