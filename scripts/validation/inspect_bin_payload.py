from pathlib import Path
import struct

bin_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/PK10R1_INC29_SOURCE_STATE.bin")
data = bin_path.read_bytes()
print(f"Total size: {len(data)} bytes")
print("Remaining size after 128 bytes:", len(data) - 128)
payload = data[128:]
print("Payload repr:", repr(payload[:100]))
