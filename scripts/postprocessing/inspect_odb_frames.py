import odbAccess
import sys

odbs = [
    ('H0', 'models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.odb'),
    ('H1', 'models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.odb'),
    ('H2', 'models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.odb')
]

for name, path in odbs:
    try:
        odb = odbAccess.openOdb(path, readOnly=True)
        print('=== ' + name + ' ===')
        for step_name in odb.steps.keys():
            step = odb.steps[step_name]
            print('Step: %s, frames: %d, totalTime: %f' % (step_name, len(step.frames), step.totalTime))
            if len(step.frames) > 0:
                print('  first frame: %d, value: %f, desc: %s' % (0, step.frames[0].frameValue, step.frames[0].description))
                print('  last frame: %d, value: %f, desc: %s' % (len(step.frames)-1, step.frames[-1].frameValue, step.frames[-1].description))
                # print all frames in Step-2
                if step_name == 'Step-2':
                    for i, f in enumerate(step.frames):
                        # print every 5th frame or around 0.00925
                        time_val = f.frameValue
                        # Step-2 load starts at 0.005, Amp2 goes from 0.1 to 0.2, so u1 = 0.005 + time_val * 0.025
                        u1_val = 0.005 + time_val * 0.025
                        if i % 10 == 0 or i == len(step.frames)-1 or abs(u1_val - 0.00925) < 0.0005:
                            print('    frame %3d: stepTime=%.6f, u1=%.6f mm, desc=%s' % (i, time_val, u1_val, f.description[:40]))
        odb.close()
    except Exception as e:
        print('Error reading %s: %s' % (name, e))
