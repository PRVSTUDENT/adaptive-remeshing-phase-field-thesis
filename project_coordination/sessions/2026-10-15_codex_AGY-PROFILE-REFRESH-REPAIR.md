# AGY smart account selection repair

Scope: external OpenClawPAD installation and installed agy-profile manager; repository scientific state and HPC authorizations unchanged. Starting commit: 5cc43720e90dbbdc0cdb983c931554ad663515e6. All pre-existing dirty paths preserved.

Findings: Refresh script used marker-based switch checks then saved global credentials. Loop inventory switched the global login for each quota probe and its 401 handler saved live credentials under the selected label. Saved accounts 1/2 share one subject and refresh token; 3/4 share another; 5 is distinct. Do not count aliases as independent capacity.

Additional empirical cause: a prior scratch/test_remaining_emails.ps1 process was still repeatedly calling CredMan.Write on backup credentials. Initial integration check failed because global credentials changed concurrently, while profile files stayed unchanged. Inspected exact script and terminated its specific credential-mutating child PID 13612. Subsequent full live scan preserved credential-manager blob hash, all five encrypted profile hashes, and active marker hash. No arbitrary processes terminated.

Repairs: quota worker receives decrypted profile only via stdin, invokes installed checker with explicit credentials, never discovers global credentials or writes tokens. Inventory reads profiles without global switching, skips duplicate subjects, excludes every alias of exhausted identity, switches only selected winner. Removed loop 401 save/agy-models recovery. Profile manager refuses cross-subject overwrite even with Force; intentional replacement requires ReplaceIdentity. Credential switch verifies actual written blob before updating marker. Refresh summary wraps timestamps and reports duplicates/auth failures explicitly.

Tests: PowerShell parser checks PASS. Mock regressions PASS: identity mismatch blocked with Force; same-subject refresh allowed; alias exclusion; auth failure skipped; selected winner only switched; weekly threshold enforced; no eligible candidate stops with zero switches. Actual loop quota-reader functions read accounts 1/2 as unavailable and 3/4/5 as OK. After stopping concurrent scan, live refresh and global/profile/marker preservation test PASS. Full autonomous loop deliberately not launched because it executes thesis/controller work outside this repair. No HPC/solver/submission actions.

Current live result: account1 AUTH_ERROR (requires account login); account2 duplicate account1; account3 OK with 100% weekly and 5h remaining; account4 duplicate account3; account5 OK with 0.2% weekly and 72.4% 5h remaining. Successful queries prove current access; future refresh-token validity of currently unexpired tokens is not established. No credentials or tokens logged/committed.

Limits: prior corrupted identities cannot be recreated automatically; five distinct profiles require individual account logins. Existing running PowerShell loops retain loaded old code and must be restarted by the user. External scripts remain at canonical installed paths; no duplicate source tree was created.

External installation SHA-256:
- C:\Users\pruth\OpenClawPAD\Refresh-AgyAccounts.ps1 : F516E0052D463833EE20504AFFA3BA269EC77B4CFEF3C37FE9DDAD4A0D0435AB
- C:\Users\pruth\OpenClawPAD\agy_profile_quota.py : 4610EB7A6BF0D977ADD86A385ED3E1BD49560FEE1B49A39548B5181BBBC39E1B
- C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1 : BDF8A6F8797907320FFE452FFF452679B467639DED9A11B228B90BA1500C897E
- C:\Users\pruth\AppData\Local\agy-profile\agy-profile.ps1 : 6E6E7A7245B96EC893C67F2557580C0EEF9FAD9F51E294C26AE6AD038F5521B0
- C:\Users\pruth\OpenClawPAD\Test-AgyAccountRefresh.ps1 : 30354617144DC99D9AEDA9B5BA73D52F32D9ECD2C11E282B676CBD0F7EE7C7D1
