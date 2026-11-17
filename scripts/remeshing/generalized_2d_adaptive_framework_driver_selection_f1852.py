"""F1852 measured driver selection, composing immutable F1849/F1846 engines.

No case identifiers or spatial crack instructions enter the selection rule.
This offline donor-history strategy does not qualify native causal adaptivity.
"""
from __future__ import print_function
import math
from scripts.remeshing import generalized_2d_adaptive_framework_damage_envelope_f1849 as damage
from scripts.remeshing import generalized_2d_adaptive_framework_f1846 as native
D_CORE=.5

def select_driver(signal,native_gate,d_core=D_CORE):
    m=float(signal['max_damage']);frac=float(signal['fraction_ge_core'])
    # Preserve measured phase-field overshoot; selection only tests the lower core threshold.
    if math.isnan(m) or math.isinf(m) or m<0 or not 0<=frac<=1:
        raise ValueError('Invalid measured damage strength')
    if abs(float(signal['d_core'])-d_core)>1e-12:
        raise ValueError('Damage measurement threshold differs from selection threshold')
    if m>=d_core:return 'CONSTRUCTED_DAMAGE_ENVELOPE'
    if not native_gate.get('accepted',False):
        raise ValueError('BLOCKED: weak damage and native signal absent or anomalous')
    return 'NATIVE_ABAQUS_STRESS_RECOVERY_ERROR'

def remesh(config,signal,native_gate,damage_donor,native_donor,output_dir,model_name):
    driver=select_driver(signal,native_gate)
    config.output_frequency='LAST_INCREMENT'
    if driver=='CONSTRUCTED_DAMAGE_ENVELOPE':
        config.sizing_driver=driver
        path=damage.AbaqusNativeRemeshingEngine.execute_native_remesh(config,damage_donor,output_dir,model_name=model_name)
    else:
        # Audited raw native donor only; no synthesized donor enters this branch.
        config.step_name=native_gate['step']
        path,records=native.AbaqusNativeRemeshingEngine.execute_native_remesh(config,native_donor,output_dir,model_name=model_name)
        if not records or any(r.get('sizing_driver')!='NATIVE_ABAQUS_STRESS_RECOVERY_ERROR' for r in records):
            raise ValueError('Native fallback unexpectedly constructed an envelope')
    return path,driver
