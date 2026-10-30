# AGY hashing and identity validation repair — 30 October 2026

Starting commit: 8988fe3e0eacc6be33f9ba9fb21aac678e0c24a3.
Bootstrap read the coordination files in order, verified an inactive session,
claimed a scoped session and preserved all pre-existing dirty work.

## Exact root causes

1. The previous installed-manager patch inserted the save-only native concurrency
   guard into Backup-IfUnsaved as well as Invoke-Save. The backup function had no
   nativeSnapshot variable. During switch/rotation it called Get-BlobHash with
   that undefined/null value. The failing overload call was
   Get-BlobHash -> SHA256.ComputeHash($bytes), originally installed line 150;
   the erroneous backup guard was at lines 314–317. A synthetic null input
   reproduced the exact "Multiple ambiguous overloads found for ComputeHash"
   exception. Byte arrays and object-array concatenation did not reproduce it.
   This was a defect introduced by the preceding Codex patch, not bad credentials.
2. Get-AgyProfileSaveBytes correctly produced a wrapped token containing nested
   id_token metadata. The installed quota worker's inspect function read only
   data['id_token'] at the root. The real account2 read-only audit reproduced
   IDENTITY_CHECK_FAILED before the fix and passes after the layout correction.
3. Live read-only Google verification establishes that the active native account
   matches saved account2 and differs from saved account1/3/4/5. Those mismatch
   protections are genuine and remain intact; they must not be bypassed.

## Corrected implementation

- Installed agy-profile.ps1: removed only the accidental guard from
  Backup-IfUnsaved, retaining the intended Invoke-Save concurrency protection.
  Get-BlobHash explicitly rejects null/empty credentials and calls the typed
  three-argument ComputeHash(byte[], offset, count). Password-export HMAC inputs
  also use explicit byte arrays and that overload; the binary format is unchanged.
- scripts/validation/AgyCredentialStores.ps1: centralized canonical account
  identity in Get-AgyCanonicalIdentity and reused it for local JWT and live
  provider identities. The identity is the first 16 lowercase hex characters of
  SHA-256 over the exact UTF-8 Google sub string. It is case-sensitive, with no
  trimming or case folding. Empty/non-string subjects are rejected at claim
  parsing. Credential blob hashes remain full SHA-256 content fingerprints;
  they are not used as a substitute for account identity.
- Installed OpenClawPAD/agy_profile_quota.py: accepts legacy root metadata,
  current nested metadata and unwrapped legacy tokens; rejects conflicting
  root/nested subjects and missing ID metadata. Canonical identity matches the
  PowerShell helper exactly. The worker normalizes a private in-memory copy for
  the checker's Windows-token parser and never rewrites a saved credential.
- Reproducible incremental installed-source changes are committed as
  agy_profile_hash_identity.patch and agy_profile_quota_identity.patch under
  scripts/validation/. Apply with git apply --unidiff-zero. Both patches passed
  apply checks against reconstructed pre-repair source copies. Exact installed
  source hashes are recorded in ARTIFACT_REGISTRY.csv; no credential hashes are
  included there.

Strict normalization, provider identity proof, Force mismatch rejection and
explicit ReplaceIdentity semantics remain unchanged. ReplaceIdentity was never
used in this session.

## Tests and failure recovery

- test_agy_quota_identity.py: 4/4 PASS. Root/nested/legacy compatibility,
  missing/conflicting identities, valid subject types, deterministic exact
  canonicalization and Python/PowerShell cross-language identity vectors.
- test_agy_profile_identity.ps1: PASS. Uses actual installed functions with a
  managed fixture CredMan class that cannot invoke Windows Credential Manager,
  and DPAPI/profile/CLI paths isolated under a new temporary directory. Covers
  save -> installed read-only quota worker verification, failed save preserving
  all four mismatched fixture profiles, the formerly failing backup branch and
  fixture switch -> store verification, known SHA-256 vector/null rejection, and
  portable password-export/import round trip.
- Existing test_agy_profile_save.ps1: PASS.
- Existing test_agy_credentials.ps1 (dot-sourced): PASS, including provider,
  native/CLI mismatch, concurrent-change, refresh and lifecycle guard regressions.
- PowerShell AST validation and scoped whitespace checks: PASS.

The new integration fixture initially failed because AST-loading selected manager
functions omitted the full script's System.Security assembly initialization.
Adding Add-Type -AssemblyName System.Security to the fixture repaired that local
test setup; the rerun and affected regression suites passed. No production
credential write was used to diagnose or repair it. Synthetic fixture folders
were retained rather than recursively deleting computed credential-like paths.

## Live read-only results

All five saved profiles now pass Refresh-AgyAccounts.ps1 -AuditOnly. This proves
local identity parsing/consistency, not live provider authentication by itself.
The subsequent actual read-only Gemini Models quota refresh returned:

| Profile | Quota status | Weekly remaining | Five-hour remaining |
|---|---|---:|---:|
| account1 | AUTH_ERROR | unavailable | unavailable |
| account2 | OK | 17.75% | 100.00% |
| account3 | AUTH_ERROR | unavailable | unavailable |
| account4 | AUTH_ERROR | unavailable | unavailable |
| account5 | AUTH_ERROR | unavailable | unavailable |

Account2 now passes read-only identity and quota validation without
reauthentication. The saved grants for account1/3/4/5 are rejected by quota
authentication; no expired/revoked distinction is inferred from that status.
Older account1 quota values are not treated as a fresh reading. Account2 remains
below the unchanged >20% weekly eligibility requirement, so no account currently
has verified eligible headroom. Automatic rotation was not restarted.

Before/after encrypted-file comparisons across the five real saved profiles
reported REAL_SAVED_PROFILES_CHANGED=0. No real save, switch, logout, native-store
repair, ReplaceIdentity, profile backup overwrite or generative model call was
invoked. The quota checker may refresh a supplied OAuth grant in memory; it did
not persist any changes to the five saved profiles.
Only AGY's explicitly scoped native/CLI/five saved accounts were inspected; no
unrelated service credentials were accessed. Tokens, subject IDs and account
emails were not printed or committed.

Next: diagnose/re-authenticate one intended rejected saved account at a time,
preserving its identity binding and backups, then obtain fresh quota readings
before enabling rotation. Do not bulk-save the active account into other labels.
