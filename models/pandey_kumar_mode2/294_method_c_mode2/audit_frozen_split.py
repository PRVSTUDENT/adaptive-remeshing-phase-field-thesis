"""Offline constitutive witness; does not execute Abaqus or change frozen physics.

Compare the energy expression literally implemented in f42_mixed_uel.for
(POS_M, mechanical quadrilateral branch) with the requested Miehe spectral
tensile energy. Strains below are tensor components; units are kN and mm.
"""
import hashlib
import json
from pathlib import Path


def audit():
    root = Path(__file__).resolve().parents[3]
    source = root / 'models/pandey_kumar_mode1/f42_mixed_uel.for'
    text = source.read_text()
    assert 'C33_0*(E11**2 + E22**2 + TWO*(E12**2))' in text
    assert 'E_POS = TR_E' in text
    mu = 210.0 / (2.0 * (1.0 + .3))
    strain = .001
    return {
        'classification': 'OFFLINE_CONSTITUTIVE_SPECIFICATION_CONFLICT',
        'solver_runs': 0,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest().upper(),
        'source': str(source.relative_to(root)),
        'witnesses': [
            {'strain': {'e11': 0, 'e22': 0, 'e12': strain},
             'frozen_POS_M_kn_per_mm2': 2 * mu * strain**2,
             'miehe_positive_energy_kn_per_mm2': mu * strain**2,
             'frozen_to_miehe_ratio': 2.0},
            {'strain': {'e11': -strain, 'e22': -strain, 'e12': 0},
             'frozen_POS_M_kn_per_mm2': 2 * mu * strain**2,
             'miehe_positive_energy_kn_per_mm2': 0.0}
        ],
        'conclusion': 'Frozen POS_M is not the requested Miehe spectral tensile energy.',
        'numerical_uncertainty': 'Whether the frozen formulation reproduces the Mode-II deflected path is untested.',
        'required_decision': 'Resolve frozen-source versus Miehe-reproduction specification before any solve.'
    }


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
