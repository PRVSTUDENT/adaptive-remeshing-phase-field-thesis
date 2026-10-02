#!/usr/bin/env python3
import subprocess
import re
from datetime import datetime

def get_job_details():
    cmd = ["qstat", "-x", "-u", "pr21vyci"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    lines = res.stdout.strip().splitlines()
    
    job_ids = []
    for line in lines:
        parts = line.split()
        if parts and (parts[0].endswith(".mmaster02") or ".mmaste" in parts[0]):
            job_ids.append(parts[0])
            
    print(f"Found {len(job_ids)} jobs in qstat -x listing.")
    
    recent_jobs_to_query = [
        "1389142.mmaster02",
        "1389086.mmaster02",
        "1389063.mmaster02",
        "1388961.mmaster02",
        "1388948.mmaster02",
        "1388946.mmaster02",
        "1388942.mmaster02",
        "1388923.mmaster02",
        "1388886.mmaster02",
        "1388878.mmaster02",
        "1388747.mmaster02",
        "1388706.mmaster02",
        "1388679.mmaster02",
        "1388675.mmaster02",
        "1388674.mmaster02"
    ]
    
    records = []
    
    for jid in recent_jobs_to_query:
        cmd_f = ["qstat", "-x", "-f", jid]
        res_f = subprocess.run(cmd_f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if res_f.returncode != 0 or not res_f.stdout.strip():
            continue
            
        text = res_f.stdout
        
        job_name = re.search(r"Job_Name\s*=\s*(.*)", text)
        job_name = job_name.group(1).strip() if job_name else "N/A"
        
        qtime_str = re.search(r"qtime\s*=\s*(.*)", text)
        qtime = qtime_str.group(1).strip() if qtime_str else None
        
        stime_str = re.search(r"stime\s*=\s*(.*)", text)
        stime = stime_str.group(1).strip() if stime_str else None
        
        mtime_str = re.search(r"mtime\s*=\s*(.*)", text)
        mtime = mtime_str.group(1).strip() if mtime_str else None
        
        queue = re.search(r"queue\s*=\s*(.*)", text)
        queue_name = queue.group(1).strip() if queue else "N/A"
        
        req_res = re.search(r"Resource_List\.select\s*=\s*(.*)", text)
        req_res_str = req_res.group(1).strip() if req_res else "1:ncpus=1:mem=16gb"
        
        req_wall = re.search(r"Resource_List\.walltime\s*=\s*(.*)", text)
        req_wall_str = req_wall.group(1).strip() if req_wall else "24:00:00"
        
        job_state = re.search(r"job_state\s*=\s*(.*)", text)
        state_str = job_state.group(1).strip() if job_state else "N/A"
        
        comment = re.search(r"comment\s*=\s*(.*)", text)
        comment_str = comment.group(1).strip() if comment else ""
        
        # Calculate queue wait duration if dates available
        # PBS date format: 'Thu Aug 13 14:56:57 2026' or similar
        wait_seconds = None
        wait_formatted = "N/A"
        
        fmt = "%a %b %d %H:%M:%S %Y"
        
        if qtime and stime:
            try:
                dt_q = datetime.strptime(qtime, fmt)
                dt_s = datetime.strptime(stime, fmt)
                wait_seconds = int((dt_s - dt_q).total_seconds())
                m, s = divmod(wait_seconds, 60)
                h, m = divmod(m, 60)
                wait_formatted = f"{h}h {m:02d}m {s:02d}s ({wait_seconds}s)"
            except Exception as e:
                wait_formatted = f"Parse err: {e}"
        elif qtime and state_str == "Q":
            try:
                dt_q = datetime.strptime(qtime, fmt)
                # Compare with now or mtime
                wait_formatted = f"Currently in queue since {qtime}"
            except Exception as e:
                wait_formatted = f"Queued ({qtime})"
                
        records.append({
            "job_id": jid,
            "job_name": job_name,
            "state": state_str,
            "queue": queue_name,
            "requested_resources": f"{req_res_str}, walltime={req_wall_str}",
            "qtime": qtime,
            "stime": stime,
            "wait_time": wait_formatted,
            "comment": comment_str
        })
        
    print(f"\nCollected {len(records)} job records.\n")
    return records

if __name__ == "__main__":
    recs = get_job_details()
    for r in recs:
        print("--------------------------------------------------")
        print(f"Job ID:               {r['job_id']}")
        print(f"Job Name:             {r['job_name']}")
        print(f"State:                {r['state']}")
        print(f"Queue:                {r['queue']}")
        print(f"Requested Resources:  {r['requested_resources']}")
        print(f"Queue Submit Time:    {r['qtime']}")
        print(f"Execution Start Time: {r['stime']}")
        print(f"Queue Wait Duration:  {r['wait_time']}")
        if r['comment']:
            print(f"Scheduler Comment:    {r['comment']}")
