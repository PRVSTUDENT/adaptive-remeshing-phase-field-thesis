p = 'project_coordination/HPC_JOB_LEDGER.csv'
lines = open(p, 'r', encoding='utf-8').readlines()
for i in range(len(lines)):
    if '1416604.mmaster02' in lines[i]:
        lines[i] = '1416604.mmaster02,M1_C4_PACKAGE92_TRANSFER,/scratch9/pr21vyci/runs/mode1_package92_c4_error_driven_transfer,mnode097/0,entry_imfdfkmq,2026-10-23T08:22:17.7570412+00:00,F,0,PACKAGE92_EXIT0_4_STEPS_RF2_113p62N_SOFTENING_MIXED_DONOR_DEFECT,c1bd24f95580e4d341cca4d62ecb50a764a35e00f62bef56d46917756c0c227b\n'
    elif '1416628.mmaster02' in lines[i]:
        lines[i] = '1416628.mmaster02,M1_C4_PACKAGE92_R1_TRANSFER,/scratch9/pr21vyci/runs/mode1_package92_r1_c4_consistent_transfer,mnode097/0,entry_imfdfkmq,2026-10-23T08:55:07.9705649+00:00,F,0,PACKAGE92_R1_EXIT0_4_STEPS_RF2_105p32N_SOFTENING_ENERGY_PASS_HISTORY_UNDERESTIMATION_DIAGNOSED,5e90a07be65a613d17c99fddef88249867523b49ecc783220e15b9af25e5f017\n'
    elif '1416642.mmaster02' in lines[i]:
        lines[i] = '1416642.mmaster02,M1_C3_PACKAGE93_INSTRUMENTED_REPLAY,/scratch9/pr21vyci/runs/mode1_package93_c3_instrumented_control,mnode097/0,entry_imfdfkmq,2026-10-23T09:31:19.4581037+00:00,R,,PACKAGE93_RUNNING_FAITHFUL_C3_INSTRUMENTED_CONTROL_ACTIVE_SET_PARITY,df04088f80ef559a93a74393f6e05003d2d1b961078c6bf6031200ffa8395953\n'
open(p, 'w', encoding='utf-8').writelines(lines)
print('HPC_JOB_LEDGER.csv updated successfully')
