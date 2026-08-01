#!/usr/bin/env python3
import json,os,re,sys
sta=open(sys.argv[1],errors="replace").read() if os.path.exists(sys.argv[1]) else ""
msg=open(sys.argv[2],errors="replace").read() if os.path.exists(sys.argv[2]) else ""
calls=open(sys.argv[3],errors="replace").read() if os.path.exists(sys.argv[3]) else ""
d={"classification":"penalty_rollback_inconclusive","independent_sta_msg_cutback_evidence":bool(re.search(r"cutback|attempt",sta+msg,re.I)),"pnewdt_requested":bool(re.search(r"F16_CALL",calls)),"common_bounds_guard_fired":bool(re.search(r"F16 BOUNDS",calls)),"required_log_fields":["KSTEP","KINC","JELEM","INPT","TIME","DTIME","trial_phase","committed_phase","trial_SVARS","committed_SVARS","SDV15","SDV16","penalty_active","PNEWDT","retry","accepted_state"]}
open("ROLLBACK_STATUS.json","w").write(json.dumps(d,indent=2,sort_keys=True)+"\n")
