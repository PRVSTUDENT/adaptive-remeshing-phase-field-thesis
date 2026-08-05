# F33 M2RMBUILD8 offline repair decision

Job `1383537.mmaster02` is classified `cae_geometry_build_contract_failed`. The primary failure was the unsupported `UNPLANNED` import. The unavailable standalone `python` cleanup command and misleading `-1` return-code sentinel were secondary defects.

Prepare immutable replacement package `M2RMBUILD8` offline. Import only Abaqus 2023 constants actually used: `ON`, `CPE4`, `STANDARD`, and `STRUCTURED`. Use preflight-verified `python3` for standalone helpers. Capture executable return codes with fail-fast temporarily disabled and represent commands not executed as `skipped`.

No submission, retry, replacement, downstream solver, or remeshing work is authorized. After clean-Linux qualification and review, request separate explicit authorization for at most one replacement submission.
