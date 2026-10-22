import shutil
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent
src_inp = repo / "models" / "pandey_kumar_mode1" / "candidate_donor_h0025_corrected.inp"
pkg76_dir = repo / "models" / "pandey_kumar_mode1" / "76_candidate_donor_h0025_visual"
pkg76_dir.mkdir(parents=True, exist_ok=True)

# 1. Read input deck
lines = src_inp.read_text(encoding="utf-8").splitlines()
out_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.strip() == "*Solid Section, elset=umatelem, material=DUMMY_ELASTIC":
        out_lines.append("*Solid Section, elset=umatelem, material=DUMMY_MAT")
        out_lines.append("1.0,")
        out_lines.append("*Material, name=DUMMY_MAT")
        out_lines.append("*User Material, constants=3")
        out_lines.append("210.0, 0.3, 1600.0")
        out_lines.append("*Depvar")
        out_lines.append("20")
        # skip old 5 lines: Solid Section, 1.0,, *Material, *Elastic, 1.0e-12, 0.3
        i += 5
        continue
    elif line.strip() == "*Element Output, elset=umatelem":
        out_lines.append(line)
        i += 1
        # next line was 'S, E'
        assert lines[i].strip() == "S, E"
        out_lines.append("SDV, S, E")
        i += 1
        continue
    elif line.strip() == "*Output, field, frequency=5":
        out_lines.append("*Output, field, frequency=1")
        i += 1
        continue
    else:
        out_lines.append(line)
        i += 1

dest_inp = pkg76_dir / "candidate_donor_h0025_visual.inp"
dest_inp.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print(f"Generated {dest_inp} with {len(out_lines)} lines")

# 2. Copy bitwise frozen UEL
uel_src = repo / "models" / "pandey_kumar_mode1" / "75_candidate_donor_h0025" / "f42_mixed_uel.for"
uel_dest = pkg76_dir / "f42_mixed_uel.for"
shutil.copy2(uel_src, uel_dest)
print(f"Copied {uel_dest}")

# 3. Copy job_notifications.sh
notif_src = repo / "models" / "pandey_kumar_mode1" / "75_candidate_donor_h0025" / "job_notifications.sh"
notif_dest = pkg76_dir / "job_notifications.sh"
shutil.copy2(notif_src, notif_dest)
print(f"Copied {notif_dest}")
