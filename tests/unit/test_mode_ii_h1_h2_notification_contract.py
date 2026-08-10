#!/usr/bin/env python3
"""Fail-Closed Notification Contract Regression Test for Mode-II H1/H2 Pair.

Verifies that PBS batch execution scripts for M2REF_H1_FRACFIX and M2REF_H2_FRACFIX:
1. Explicitly specify `#PBS -m abe`
2. Specify exact approved 2-recipient email configuration (`#PBS -M`)
3. Contain no missing, single, or duplicate recipients
4. Reject defective single-recipient or missing directive configurations.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H1_PBS = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.pbs"
H2_PBS = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.pbs"

APPROVED_RECIPIENTS = {
    "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de",
    "pr21vyci@mailserver.tu-freiberg.de",
}

def parse_pbs_notification_directives(path: Path):
    mail_points = None
    recipients = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#PBS -m "):
            mail_points = line.split(None, 2)[2].strip()
        elif line.startswith("#PBS -M "):
            raw_recips = line.split(None, 2)[2].strip()
            recipients.extend([r.strip() for r in raw_recips.split(",") if r.strip()])

    return mail_points, recipients

def validate_notification_contract(path: Path):
    mail_points, recipients = parse_pbs_notification_directives(path)

    if mail_points != "abe":
        raise ValueError(f"{path.name}: mail_points must be 'abe', found {mail_points!r}")

    if len(recipients) != 2:
        raise ValueError(f"{path.name}: recipient count must be exactly 2, found {len(recipients)}")

    if len(recipients) != len(set(recipients)):
        raise ValueError(f"{path.name}: duplicate recipients detected in {recipients}")

    if set(recipients) != APPROVED_RECIPIENTS:
        raise ValueError(f"{path.name}: recipient set {set(recipients)} does not match approved set {APPROVED_RECIPIENTS}")

    return True

class TestNotificationContractRegression(unittest.TestCase):

    def test_h1_notification_contract_pass(self):
        self.assertTrue(H1_PBS.exists(), f"{H1_PBS} does not exist")
        self.assertTrue(validate_notification_contract(H1_PBS))

    def test_h2_notification_contract_pass(self):
        self.assertTrue(H2_PBS.exists(), f"{H2_PBS} does not exist")
        self.assertTrue(validate_notification_contract(H2_PBS))

    def test_defective_configurations_rejected(self):
        # 1. Missing #PBS -m abe
        bad_script_no_m = Path("test_bad_no_m.pbs")
        bad_script_no_m.write_text("#!/bin/bash\n#PBS -N BAD\n#PBS -M a@b.de,c@d.de\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                validate_notification_contract(bad_script_no_m)
        finally:
            if bad_script_no_m.exists(): bad_script_no_m.unlink()

        # 2. Single recipient
        bad_script_single = Path("test_bad_single.pbs")
        bad_script_single.write_text("#!/bin/bash\n#PBS -N BAD\n#PBS -m abe\n#PBS -M pr21vyci@mailserver.tu-freiberg.de\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                validate_notification_contract(bad_script_single)
        finally:
            if bad_script_single.exists(): bad_script_single.unlink()

        # 3. Duplicate recipient
        bad_script_dup = Path("test_bad_dup.pbs")
        bad_script_dup.write_text("#!/bin/bash\n#PBS -N BAD\n#PBS -m abe\n#PBS -M pr21vyci@mailserver.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                validate_notification_contract(bad_script_dup)
        finally:
            if bad_script_dup.exists(): bad_script_dup.unlink()

if __name__ == "__main__":
    unittest.main()
