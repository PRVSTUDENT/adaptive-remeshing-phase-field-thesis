# AGY controller profile collision repair

User observed expected account1 / detected account5 at POST_AGY. Prior Codex recovery controller PID 10528 was still alive waiting at the PAD bridge while the user launched another controller. Both used global AGY profile state. Stopped only PID 10528 after verifying it had no AGY worker child and the scientific session was released. No scheduler operation or scientific submission occurred.

Added a per-Windows-user global named mutex before profile initialization to installed controller and SmartProfiles template, held through the entire script with finally release/disposal. A second controller fails before smart selection or AGY execution; abandoned locks recover after a crashed owner. Existing POST_AGY drift protection remains intact. The repair installer preserves the change idempotently.

Validation: both complete scripts parsed without errors. Held the real mutex and launched the full installed script in a second PowerShell: correctly rejected before startup/profile switching. Released and reacquired mutex successfully. Repair idempotence passes both files. Initial test incorrectly treated harmless pre-lock DEBUG PROFILE output as profile mutation; corrected assertion to detect actual switching/startup and reran successfully.

No controller automatically restarted. User may rerun the original command with smart profile selection enabled. Recovery should inspect current F1530 state rather than replay previous submissions. Pre-existing unrelated dirty files preserved.
