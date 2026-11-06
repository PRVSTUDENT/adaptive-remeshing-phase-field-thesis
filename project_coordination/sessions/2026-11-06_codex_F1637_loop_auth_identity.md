# F1637 real loop handshake and authentication diagnosis

One normal Start-Verified-MethodCLoop -MaxTurns 40 launch occurred at 18:50:57 local on 6 November. Launcher PID 23296, controller PID 20992. Fresh F1636 run 8f718381-2c4d-4320-b7fa-ddcd8e1201f4 was created as PENDING, turn 1, process_id=0. Startup reported authentication grant refresh success, but subsequent guarded identity recovery failed.

Canonical controller published HND-SUP-07fa925dfd54467db134a3b4af297bb8 at 18:51:41 (72220 characters). Existing PAD returned a matching status OK response copied at 17:52:37.322Z. Canonical bridge detected it after 58 seconds, accepted/extracted 1453 characters and archived the transaction. This is a genuine completed transport exchange, not just a dry run. Returned JSON correlation matches the handoff and requested DIAGNOSE of AUTH_RECOVERY_REQUIRED. No second request, manual replay or PAD restart occurred.

Archived request SHA-256 312312B49F45A0B2D65D3227F816C057CE1EF3143D79D55EF26BD4F7F253AD46; response SHA-256 F88C7F7378FD1239325F825E12E31B694EE1B3DE8FA1B2AD7D5ABFA54D3DDDC1. Files remain under C:/Users/pruth/OpenClawPAD/ChatGPTBridge/archive with timestamp 20261106_185141. Matching correlation/freshness and canonical transaction consumption were observed. This is not a cryptographically signed scientific approval.

Durable auth recovery state: AUTH_RECOVERY_REQUIRED, safety_blocked=true, selected profile empty, attempted account2, refresh_attempted=true, outcome IDENTITY_MISMATCH. File auth_recovery/8F3911DDB501C8406788F8C40E34410F11A06BF150ACB154E0D628BD44CD553E-5304C09CF2F13B2F.json remains untouched.

Executed one read-only check using existing AgyCredentialStores.ps1 readers, parser and provider-identity lookup. Result: profile account2; native_saved_identity_match=false; cli_saved_identity_match=true; provider_status=IDENTITY_MISMATCH; provider_saved_identity_match=false. No tokens, credentials or personal provider identity were printed. No credential mutation or account switch was performed by this diagnostic. Identity mismatch is verified; token expiration is not established.

Controller and launcher exited. No research worker was dispatched, no scientific evaluation completed, no PBS jobs submitted. F1636 stays registered and PENDING. No safety reset or retry is appropriate. The user must authenticate the intended profile through the official interactive AGY interface, then use supported local identity verification/recovery before a new controller start. Do not relaunch while the block persists.

Computer-use inspection was attempted read-only but native helper pipe was unavailable on both calls; no app input or flow modification occurred. Transport success was established from canonical receipt and archive, not UI inference.

Published F1635 registration in commit 9901f2ad on existing feature branch mode2-pandey-kumar-reproduction; prior eb61141 preserved. This closeout preserves original F1608 runtime evidence, new F1636 PENDING checkpoint, scientific/HPC ledgers, and unrelated dirty work.
