from pathlib import Path

repo_root = Path(r"D:\Master thesis\Adaptive remeshing")
registry_file = repo_root / "project_coordination/ARTIFACT_REGISTRY.csv"

lines = [
    '"F1597-97211912-f161-46b2-9cdf-d7f0c3e81913-2026-10-25_gemini-antigravity_F1597_97211912-f161-46b2-9cdf-d7f0c3e81913.md","Mode-I","project_coordination/sessions/2026-10-25_gemini-antigravity_F1597_97211912-f161-46b2-9cdf-d7f0c3e81913.md","verified_diagnostic_evidence","verified","gemini-antigravity","7c216042c242c86d3184f4c020d5f6ee2d850a8f","80ACA595F5533294D26C60ACF1FCDF589E7597BA22CBE9B3B3C3EE2B0FBDCBBF","","Research preparation; not a transfer qualification"\n',
    '"F1597-97211912-f161-46b2-9cdf-d7f0c3e81913-preparation-97211912-f161-46b2-9cdf-d7f0c3e81913.json","Mode-I","results/validation/preparation-97211912-f161-46b2-9cdf-d7f0c3e81913.json","verified_diagnostic_evidence","verified","gemini-antigravity","7c216042c242c86d3184f4c020d5f6ee2d850a8f","DDBA81CA485FDB2BABEE8C6C5D51662C9B6BBD5A3DC8BE1BB695EA4059B0DBBE","","Research preparation; not a transfer qualification"\n',
    '"F1597-97211912-f161-46b2-9cdf-d7f0c3e81913-r13_autonomous_continuation_summary.json","Mode-I","results/validation/mode1_f1597/r13_autonomous_continuation_summary.json","verified_diagnostic_evidence","verified","gemini-antigravity","7c216042c242c86d3184f4c020d5f6ee2d850a8f","AA4D898FAA437748F2585E52E25528A84F212196AA54694AC389B960B5336092","","R13 autonomous active-set continuation cluster execution summary (Job 1417292)"\n'
]

with open(registry_file, "a", encoding="utf-8") as f:
    f.writelines(lines)

print("Appended entries to ARTIFACT_REGISTRY.csv successfully!")
