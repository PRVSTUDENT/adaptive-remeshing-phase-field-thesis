# Diagnostic Source Changelog

Source: copied from `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/SingleNotch_v2.for`.

## Changes

- Added read-only scalar temporaries for diagnostic values.
- Added target-gated calls after U1 uploads completed `SDV(1)`/`SDV(2)` into `USRVAR(...,15/16,ip)`.
- Added target-gated calls after U2 uploads copied/retained phase into `USRVAR(...,14,ip)`.
- Added target-gated calls after UMAT copies `USRVAR` into visualization `STATEV`.
- Added `DIAG_LOG_RECORD` and `DIAG_IS_TARGET`, using `GETOUTDIR` and `diagnostic_targets.inc`.

## Non-Intrusiveness Rationale

The logging routines read already computed values and append CSV rows only for
selected target element/IP pairs. They do not assign to `STATEV`, `SVARS`,
`USRVAR`, `RHS`, `AMATRX`, `PROPS`, Abaqus flags, solver controls, coordinates,
or loads. The only side effect is a flushed diagnostic CSV under the Abaqus
scratch working directory.

## Stage Codes

- `101`: U1 completed phase/history upload.
- `201`: U2 copied or retained phase upload.
- `301`: CPS4/UMAT visualization copy.
