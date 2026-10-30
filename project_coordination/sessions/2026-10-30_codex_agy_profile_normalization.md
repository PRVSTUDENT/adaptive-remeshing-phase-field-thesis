# agy-profile save identity repair — 30 October 2026

Starting commit: 29b2ff991f6cd06539e297dc14b7dc647b757bae.
Bootstrap read the coordination files in order, verified an inactive session,
claimed a scoped Codex session and preserved pre-existing dirty work.

## Cause established

Get-Command resolves agy-profile to
C:/Users/pruth/AppData/Local/agy-profile/agy-profile.ps1, with a .cmd wrapper
alongside it. That script loads scripts/validation/AgyCredentialStores.ps1.

Read-only shape inspection, with credential values suppressed, established:

- Native Credential Manager: wrapped access/refresh grant, no root or nested ID.
- Saved account1/account2: wrapped grant and root ID metadata.
- CLI file: wrapped grant and nested ID metadata.

The installed Invoke-Save called strict ConvertTo-AgyCredentialToken through
Get-CredentialSubject with no source label. Thus a native grant missing only ID
metadata produced source=unspecified, stage=ID_TOKEN_MISSING. The strict execution
guard is behaving as designed; save was missing a separate verified preparation
path. No inference about quota follows from successful authentication.

## Repair

Added Get-AgyProfileSaveBytes to the shared helper. Its existing-ID path preserves
the input bytes. For a native grant without ID metadata, it:

1. Reads CLI identity metadata without changing that file.
2. Uses the existing bounded Google userinfo lookup to prove the native access
   grant belongs to the same subject as the CLI metadata.
3. Rejects provider failure/mismatch, missing metadata, authentication-method
   mismatch and concurrent CLI changes.
4. Adds only the proven ID metadata to an in-memory candidate, retaining the
   native access token, refresh token and expiry. It neither refreshes tokens nor
   writes native, CLI or saved-profile stores.

Patched the installed manager's save path to prepare that candidate before any
profile write, label saved/native sources explicitly and recheck the original
native snapshot immediately before saving. Existing identity mismatch protection
remains: Force cannot replace another account identity. The separate explicit
ReplaceIdentity behavior is unchanged. Strict normalization and execution guards
were not relaxed. Exceptions suppress credential/provider payloads.

The installed source change is reproducible via
scripts/validation/agy_profile_save_identity.patch, an incremental patch on the
already installed manager version. Installed script SHA-256:
DCE0D5A4FCF9D17D6B4009AE16DEECECB09F2B3E03C045CF818ECCB993EE4C62.

## Verification

- New test_agy_profile_save.ps1 PASS: current-grant preservation, proof required,
  no store writes, provider/metadata/concurrent-file rejection, credential-safe
  errors, and the actual installed Invoke-Save function executed with synthetic
  stores. Synthetic save succeeds; wrong saved identity and native drift stop
  before profile or marker writes.
- Existing test_agy_credentials.ps1 PASS when dot-sourced. Covers strict layout
  checks, wrong-account rejection, provider verification, lifecycle guards,
  expired native recovery, concurrent change, failed readback and HTTP behavior.
- Helper and installed manager PowerShell AST parsing PASS; scoped whitespace
  check PASS.
- Live read-only Get-AgyProfileSaveBytes PASS: Google verified the current native
  grant and its subject matched saved account2. Only a temporary in-memory
  candidate was produced; credential byte buffers were cleared afterward.

Initial invocation of the old credential test using the call operator failed
with AGY_CREDENTIAL_REPAIR_IDENTITY_CONFLICT on synthetic data. Diagnosis: that
test declares local mocks then replaces them using global mocks, so its fixture
requires dot-sourcing in the test shell. Dot-sourcing passed without changes to
the old test or production guard. This was a test-scope issue, not a live login
failure, and no blind save retry occurred.

## Quota and scope

The current controller defaults still require strictly greater than 20% long
window and strictly greater than 20% five-hour headroom. They were not changed.
Fresh bounded saved-profile quota queries for account1 through account5 all
returned UNRESOLVED in this session. No account is declared quota-eligible; the
older user-provided percentages were not treated as fresh measurements.

No real save, save -Force, switch, logout, credential repair/write, profile
replacement or generative model call was invoked. Existing _unsaved backups and
saved profiles were not modified. No credential data or credential hashes are
included in this report or the commit. The manager source hash above is code.

Next: the normal save command can use the corrected path while the current grant
and CLI metadata remain verifiable. Quota telemetry needs separate diagnosis
before controller execution; authentication success alone does not qualify quota.

Patch format note: the installed-manager patch uses zero context (git apply --unidiff-zero), avoiding whitespace-only context warnings while preserving exact source edits.
