# Stage F11 batch preparation

Stage F11 freezes the byte-identical F10 minimal decks and changes only
identical diagnostic-output infrastructure. It uses explicit integration of
elastic, crack, history-driven, and penalty quantities and trapezoidal RF--U
work; no exact global variational-energy claim is made.

The compact `N_ELEM=23` mapping is retained. The baseline diagnostic penalty
channels are zero. Candidate diagnostics are assigned inside the exact
governing penalty branch. The bounded prior-state log and multi-case
directional-derivative audit are preflight requirements.

The CAE-only wrapper resolves its core, source ODB, and deck solely from
`F11_RUNTIME_DIR` and contains no `__file__` dependency.

Validation before preparation commit:

- 25 targeted Stage F8--F11 tests passed;
- all seven new F11 tests passed;
- the full suite collected 320 tests, with 276 passes and 44 unrelated
  workstation/pre-existing failures (primarily invalid subprocess handles
  under the GUI Python executable and stale historical assertions);
- both exact F11 Fortran sources compiled and linked under Abaqus 2023 with
  ifort 2021.13;
- all three Abaqus-side Python files byte-compiled;
- static H2, static MISESERI, bootstrap consistency, shell syntax, JSON, and
  candidate directional-derivative checks passed.
