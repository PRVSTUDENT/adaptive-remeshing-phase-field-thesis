# H2 endpoint-resolution closeout — job 1388330.mmaster02

Job `M2H2ENDPOINT` finished with PBS state `F`, exit status `1`, CPU `04:25:49`, walltime `04:26:30`, memory `2330664kb`, and VMEM `3624500kb`. It did not exhaust the qualified `24:00:00` walltime. Abaqus completed Step 2 increment 1906, with one cutback, and retained the last converged output at `U1=0.009762500412762165 mm`. The terminal cause was numerical divergence: `THE SOLUTION APPEARS TO BE DIVERGING`, followed by `FIXED TIME INCREMENT IS TOO LARGE`. The prescribed `0.010000 mm` endpoint was not reached.

## Identity and reproduction

- Input SHA256: `c9a3f496cf2cb0daa455cfae31f5bd699b56f3b410f0a7f2a12014b2718be5b0`.
- Historical H2 input has the same SHA256 and is byte-identical.
- UEL SHA256: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`.
- `NPHYS=33852`.
- On `0 <= U1 <= 0.00925000011920929 mm`, old and new H2 are identical in the saved RF–U and dmax histories: normalized L2 `0%`, work difference `0%`, maximum absolute RF difference `0 kN`, and endpoint dmax difference `0`.
- Damage initiation is also identical: first saved `dmax>=0.5` at `0.00774999987334013 mm` and `dmax>=0.9` at `0.00800000037997961 mm`.

## New H2 endpoint science

- Maximum RF1: `0.358134001493454 kN` at `U1=0.009499999694526196 mm`; this is an interior peak.
- Final RF1: `0.35292819142341614 kN`.
- Origin-OLS initial stiffness (`0<U1<=0.002 mm`): `45.8741275290422 kN/mm`.
- Final-frame dmax: `0.9998552203178406`; the global maximum over all frames is `0.9999661445617676`.
- Global phase bounds: `[0, 0.9999661445617676]`; overshoot `0`.
- SDV16 maximum `2303.837646484375`; negative transitions `0`.
- SDV15 negative transitions `8`; worst decrease `-0.00039768218994140625`.
- `max|SDV14-SDV15|=0`, `mean|SDV14-SDV15|=0`.

## Revised convergence

The H1/H2 common endpoint is `0.00963249988853931 mm`. On that domain, H2-vs-H1 normalized RF L2 is `0.535998817939661%`; absolute work difference is `0.287073089313041%` (H2 lower); endpoint RF difference is `-1.44529229172058%`; endpoint dmax difference is `+0.00194786934208391`; and stiffness difference is `-0.0639956304353311%`. H1 and H2 retain identical `dmax>=0.5` initiation at the saved `0.00775 mm` frame, while H1 reaches `dmax>=0.9` at `0.00850 mm` versus H2 at `0.00800 mm`.

The frozen matched-state crack-path Hausdorff at `0.00925 mm` remains `0.005443 mm`, exceeding the `0.00375 mm` gate. An exact Hausdorff value at the new common endpoint cannot be reported because H2 has no saved field frame at `0.0096325 mm`; its nearest saved detailed state is `0.0097500 mm`, outside the H1 domain. Direct phase-field fracture energy was not present in the ODB history outputs, so energy comparisons are unavailable without a separately validated reconstruction method.

H2 did not reach `0.010 mm`; therefore a true H0/H2 full-path comparison and final `0.010 mm` crack contour do not exist. For context only, on the available H0/H2 domain through `0.0097625004 mm`, normalized RF L2 is `1.89115229719463%` and absolute work difference is `1.3039606092402%`.

## Cost

- Old H2: CPU `14455 s`, walltime `14501 s`.
- New H2: CPU `15949 s`, walltime `15990 s`.
- Additional runtime: CPU `1494 s`; walltime `1489 s` (`00:24:49`).
- New H2/H0 CPU ratio: `7.9745` (`H0=2000 s`).
- New H2/H1 CPU ratio: `2.9343` (`H1=5434 s`).
- New H2/MM CPU ratio: `97.25` (`MM=164 s`).
- New H2/PK5 CPU ratio: `43.58` (`PK5=366 s`).

## Scientific classification

- Scheduler-censoring question: resolved — termination was scientific/numerical, not scheduler-driven.
- Old/new H2 reproduction: pass exactly at recorded-history precision.
- H2 global peak: identified as an interior peak.
- Global H0/H1/H2 peak convergence: unresolved because H1 remains terminally incomplete.
- Full post-peak uniform convergence: unresolved; neither H1 nor H2 completed the prescribed path.
- Matched-state crack-path convergence: fail at the frozen gate.
- Complete uniform fracture reference: not established.
