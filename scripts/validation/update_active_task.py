import json

path = 'project_coordination/ACTIVE_TASK.json'
with open(path, 'r', encoding='utf-8') as f:
    task = json.load(f)

task['active_pbs_job_ids'] = ['1416642.mmaster02']
for jid in ['1416604.mmaster02', '1416628.mmaster02']:
    if jid not in task['completed_pbs_job_ids']:
        task['completed_pbs_job_ids'].append(jid)

task['phase'] = (
    "Evaluated Package 92-R1 Exit 0 solver completion (Job 1416628, 4 steps, 0 cutbacks, RF2=105.32 N, -31.5% softening drop) "
    "and proved that single-frame displacement reconstruction underestimated running maximum history H at 1,067 / 10,600 Gauss points (by up to 1.0964 kN/mm^2). "
    "Formulated faithful Package 93 instrumented C3 control with Layer 3 companion elements (2,650 CPE4 quads, IDs 5301..7950) "
    "and exact Package 90-R1 active-set boundary conditions (2,221 clamped far-field nodes, 548 free crack-band nodes, 0 healing nodes). "
    "Passed 6/6 unit tests, completed cluster interactive datacheck Exit 0, and submitted qualified job to PBS entry_imfdfkmq as Job 1416642.mmaster02 under the Job-First / Report-After policy."
)
task['status'] = 'PREPARATION_COMPLETE'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(task, f, indent=4)

print('ACTIVE_TASK.json updated successfully')
