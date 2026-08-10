#!/bin/bash
# Guarded submit wrapper for M2STATE_FRACFIX_RESTART2
set -euo pipefail

EXPECTED_INP_SHA="15deda2fe6aac8c153f5df043ca509ced4d9437e977353f194354e553043f22c"
EXPECTED_UEL_SHA="0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"
EXPECTED_PBS_SHA="50288c53cb47ef3e5cfff7f06deaa4c9dc232434e333800cd091819b8d685ed1"
EXPECTED_ART_SHA="d537063702e502b7fd5db60312cdc5b09e2221d02e5217eb1b7052c63f623052"
EXPECTED_TRANS_SHA="9006f98c59e6de37c173b3441051708805a954fa80db0eb41f5b3ef4c61aa0ff"

ACTUAL_INP_SHA=$(sha256sum M2STATE_FRACFIX_RESTART2.inp | awk '{print $1}')
ACTUAL_UEL_SHA=$(sha256sum f42_mixed_uel.for | awk '{print $1}')
ACTUAL_PBS_SHA=$(sha256sum M2STATE_FRACFIX_RESTART2.pbs | awk '{print $1}')
ACTUAL_ART_SHA=$(sha256sum STATE_TRANSFER_ARTIFACT.json | awk '{print $1}')
ACTUAL_TRANS_SHA=$(sha256sum TRANSFER_MANIFEST.json | awk '{print $1}')

if [ "$ACTUAL_INP_SHA" != "$EXPECTED_INP_SHA" ]; then echo "INP SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_UEL_SHA" != "$EXPECTED_UEL_SHA" ]; then echo "UEL SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_PBS_SHA" != "$EXPECTED_PBS_SHA" ]; then echo "PBS SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_ART_SHA" != "$EXPECTED_ART_SHA" ]; then echo "ARTIFACT SHA mismatch!"; exit 1; fi
if [ "$ACTUAL_TRANS_SHA" != "$EXPECTED_TRANS_SHA" ]; then echo "TRANSFER MANIFEST SHA mismatch!"; exit 1; fi

echo "Preflight check PASS. Submitting M2STATE_FRACFIX_RESTART2 to PBS..."
qsub M2STATE_FRACFIX_RESTART2.pbs
