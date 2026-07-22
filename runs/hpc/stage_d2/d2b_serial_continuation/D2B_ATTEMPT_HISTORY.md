# D2B Attempt History

Stage D2B was submitted exactly once in this closeout. D2C and D2D were not submitted.

| Job | Result | Note |
|---|---:|---|
| `1376819.mmaster02` | `Exit_status=10` | Abaqus compiled and entered all three steps, but Standard exited with solver return code `1`. The message file reports `TOO MANY INCREMENTS NEEDED TO COMPLETE THE STEP` during the tiny continuation. No `D2B.ok` was written. |

Classification after this attempt: `stage_d2b_solver_fail`.

Corrective preparation: increase the maximum increment allowance for the D2B release/continuation steps before any future authorized D2B rerun. This is a deck-control correction, not a change to transferred field values, transfer table values, or element/IP mapping.
