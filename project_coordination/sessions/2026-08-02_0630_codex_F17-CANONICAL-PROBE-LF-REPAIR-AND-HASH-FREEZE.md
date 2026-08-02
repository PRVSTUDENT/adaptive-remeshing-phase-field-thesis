# F17 canonical probe-LF repair and hash freeze

- Starting commit: `720e42ae132d24885a144b247f0eb5395cd26227`
- Preparation commit: `b68fae8bb7752d5922d55144f3ce25fa5a8d674a`
- Classification: `f17_clean_linux_manifest_reproducibility_failed_adaptive_legacy_manifest`

The generating Linux clone used Git 2.43.0 with `core.autocrlf=false`.
The probe PBS was repaired from 2,242 to 2,243 bytes by one EOF LF append;
its SHA-256 is `10451ed7...`. Probe manifests passed 12/12.

The second clean worktree `/home/pruth_ubuntu/f17_canonical_proof_b68fae8`
passed both probe manifests and adaptive `F17_SHA256SUMS` 11/11. Adaptive
legacy `SHA256SUMS` failed five metadata entries. No authorization or
scheduler operation followed; qsub attempts and job IDs are zero/none.
