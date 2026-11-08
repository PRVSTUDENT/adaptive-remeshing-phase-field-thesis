import hashlib
import os
import datetime

reg_path = 'project_coordination/ARTIFACT_REGISTRY.csv'
now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
task_id = 'F1687-METHOD-A-ENDENERI-CONTROL-AND-DIFFERENTIAL-RULE-GENERALIZATION'
agent = 'gemini-antigravity'

new_arts = [
    ('project_coordination/sessions/2026-11-08_chatgpt_review_f1687_closeout.md', 'independent_review_record', 'ChatGPT independent review record approving Task F1687 closeout and H1/H2 falsifications (HND-d12747caae66)'),
    ('project_coordination/task_definitions/F1688-PANDEY-KUMAR-SEC43-REPRODUCTION-CONTROL.json', 'task_definition', 'Task definition for Pandey-Kumar Section 4.3 reproduction control test mandated by HND-d12747caae66')
]

with open(reg_path, 'a', encoding='utf-8') as f:
    for path, atype, desc in new_arts:
        if os.path.exists(path):
            size = os.path.getsize(path)
            with open(path, 'rb') as pf:
                h = hashlib.sha256(pf.read()).hexdigest().upper()
            f.write(f'{path},{atype},{h},{size},{agent},{task_id},"{desc}",{now_iso}\n')
            print(f'Registered: {path}')
