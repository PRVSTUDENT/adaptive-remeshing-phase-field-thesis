#!/bin/bash
# Guarded submit wrapper for M2STATE_FRACFIX_RESTART1
set -euo pipefail

EXPECTED_INP_SHA="211bcbc7aeade414818b1127656b054e16c1425d02321a474a8b63d5afdb181b"
EXPECTED_UEL_SHA="0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"
EXPECTED_PBS_SHA="e0177e8f80a70aaec263b6b5bd34624b48b7e6b53d9133c4fb26e65dd42b5209"
EXPECTED_ART_SHA="71b62a941abfa702aa7a327789fcbc4ffe158ec3bdba1a1fcbb0c6e9515b238e"
EXPECTED_TRANS_SHA="b60ab220605da5a4583149a725a53a7bc79f812b3dccee8e6d2c79f08aa7dfb8"

ACTUAL_INP_SHA=$(sha256sum M2STATE_FRACFIX_RESTART1.inp | awk "{print \$1}")
ACTUAL_UEL_SHA=$(sha256sum f42_mixed_uel.for | awk "{print \$1}")
ACTUAL_PBS_SHA=$(sha256sum M2STATE_FRACFIX_RESTART1.pbs | awk "{print \$1}")
ACTUAL_ART_SHA=$(sha256sum STATE_TRANSFER_ARTIFACT.json | awk "{print \$1}")
ACTUAL_TRANS_SHA=$(sha256sum TRANSFER_MANIFEST.json | awk "{print \$1}")

if [ "$ACTUAL_INP_SHA" != "$EXPECTED_INP_SHA" ]; then echo "INP SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_UEL_SHA" != "$EXPECTED_UEL_SHA" ]; then echo "UEL SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_PBS_SHA" != "$EXPECTED_PBS_SHA" ]; then echo "PBS SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_ART_SHA" != "$EXPECTED_ART_SHA" ]; then echo "ARTIFACT SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_TRANS_SHA" != "$EXPECTED_TRANS_SHA" ]; then echo "TRANSFER MANIFEST SHA mismatch!"; exit 1; fi

echo "Preflight check PASS. Submitting M2STATE_FRACFIX_RESTART1 to PBS..."
qsub M2STATE_FRACFIX_RESTART1.pbs
