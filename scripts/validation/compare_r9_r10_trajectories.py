#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

r9_p = Path("models/pandey_kumar_mode1/171_c6_package171_r9_c3_0_adaptive_reequilibration/evidence/1420215.mmaster02/live_iteration_telemetry.json")
r10_p = Path("models/pandey_kumar_mode1/171_c6_package171_r10_c3_0_adaptive_reequilibration/evidence/1420261.mmaster02/live_iteration_telemetry.json")

with open(r9_p, "r", encoding="utf-8") as f:
    r9 = json.load(f)
with open(r10_p, "r", encoding="utf-8") as f:
    r10 = json.load(f)

print(f"{'Iter':<5} | {'R9 Delta d':<11} | {'R10 Delta d':<11} | {'R9 Delta u':<11} | {'R10 du_raw':<11} | {'R10 du_rel':<11} | {'R9 Delta H':<11} | {'R10 Delta H':<11}")
print("-" * 95)
for k in range(85, 141, 5):
    it9 = r9[k-1]
    it10 = r10[k-1]
    dd9 = f"{it9['delta_d']:.3e}"
    dd10 = f"{it10['delta_d']:.3e}"
    du9 = f"{it9['delta_u']:.3e}" if it9.get('delta_u') is not None else "None"
    du10_raw = f"{it10.get('delta_u_raw'):.3e}" if it10.get('delta_u_raw') is not None else "None"
    du10_rel = f"{it10.get('delta_u_relaxed'):.3e}" if it10.get('delta_u_relaxed') is not None else "None"
    dh9 = f"{it9['delta_h']:.3e}" if it9.get('delta_h') is not None else "None"
    dh10 = f"{it10['delta_h']:.3e}" if it10.get('delta_h') is not None else "None"
    print(f"{k:<5d} | {dd9:<11} | {dd10:<11} | {du9:<11} | {du10_raw:<11} | {du10_rel:<11} | {dh9:<11} | {dh10:<11}")

def calc_rho(series):
    return (series[-1] / series[0]) ** (1.0 / (len(series) - 1))

r9_w = r9[125:140]
r10_w = r10[125:140]
print("\n--- Stationary Active-Set Window (Iter 126-140, 15 iterations) ---")
print(f"R9  rho(Delta d):     {calc_rho([x['delta_d'] for x in r9_w]):.5f}")
print(f"R10 rho(Delta d):     {calc_rho([x['delta_d'] for x in r10_w]):.5f}")
print(f"R9  rho(Delta u):     {calc_rho([x['delta_u'] for x in r9_w]):.5f}")
print(f"R10 rho(du_raw):      {calc_rho([x['delta_u_raw'] for x in r10_w]):.5f}")
print(f"R10 rho(du_relaxed):  {calc_rho([x['delta_u_relaxed'] for x in r10_w]):.5f}")
print(f"R9  rho(Delta H):     {calc_rho([x['delta_h'] for x in r9_w]):.5f}")
print(f"R10 rho(Delta H):     {calc_rho([x['delta_h'] for x in r10_w]):.5f}")

r9_s2 = r9[89:140]
r10_s2 = r10[89:140]
print("\n--- Full Stage 2 Window (Iter 90-140, 51 iterations) ---")
print(f"R9  rho(Delta d):     {calc_rho([x['delta_d'] for x in r9_s2]):.5f}")
print(f"R10 rho(Delta d):     {calc_rho([x['delta_d'] for x in r10_s2]):.5f}")
print(f"R9  rho(Delta u):     {calc_rho([x['delta_u'] for x in r9_s2]):.5f}")
print(f"R10 rho(du_raw):      {calc_rho([x['delta_u_raw'] for x in r10_s2]):.5f}")
print(f"R10 rho(du_relaxed):  {calc_rho([x['delta_u_relaxed'] for x in r10_s2]):.5f}")
print(f"R9  rho(Delta H):     {calc_rho([x['delta_h'] for x in r9_s2]):.5f}")
print(f"R10 rho(Delta H):     {calc_rho([x['delta_h'] for x in r10_s2]):.5f}")

