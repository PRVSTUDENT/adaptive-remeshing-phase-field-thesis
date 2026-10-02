# Pre-Job Anti-Deviation Card: PK_M1_ADAPT_2PCT_13K_ENERGY

**Model Identity**: 2.0% Error-Target Efficiency-Calibrated Adaptive Mode-I Fracture Solve (13,897 Finite Elements)  
**Literature Reference Target**: Pandey, P., & Kumar, S. (2025). CMES, Vol. 144, No. 3, pp. 3251–3276. (Reported $\sim 13{,}941$ elements at literal 1% target)  
**Project Variant Qualification**: Efficiency-calibrated 2% sensitivity configuration reproducing literature element-count scale ($\Delta = 0.32\%$) and crack-tip resolution ($h_{\text{tip}} = 0.81\,\mu\text{m}$), evaluated as a project variant rather than literal 1% reproduction.  
**Lineage**: 2,906-Element Coarse Baseline with Corrected Poisson Contraction BC -> Native CAE Adaptive Remeshing (`errorTarget=2.0%`, `h_min=0.001`, `h_max=0.020`)  
**Physical Discretization**: 13,897 Finite Elements ($13,506$ quads, $391$ tris), 13,884 nodes  
**Layered Representation**: 41,691 Layered Elements ($13,897$ Phase U1/U3 $+ 13,897$ Disp U2/U4 $+ 13,897$ Companion CPE4/CPE3)  
**Formulation**: `f42_mixed_uel.for` (`ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`)  
**Thermodynamic Work Boundary Target**: $N_{\text{phys}} = 13897.0$  
**Material & Phase Field Parameters**: $E = 210.0\,\text{kN/mm}^2$, $\nu = 0.3$, $l_0 = 0.0075\,\text{mm}$, $G_c = 0.0027\,\text{kN/mm}$, $\eta = 1.0 \times 10^{-7}$  
**Execution Mode**: 1-CPU Serial, Shared-Memory (`double=both`, `cpus=1`, `memory=16gb`)  
**Queue**: `normal_imfdfkmq` via `entry_imfdfkmq` (Cluster: `cl2-login1.hrz.tu-freiberg.de`, PBS Job ID: `1409846.mmaster02`)  
**Dual-Channel Notifications**: PBS Mail (`-m abe`) + Telegram Webhook Trap (`job_notifications.sh`)  
**Output Protocol**: All_elem SDV17..20 Companion Layer Output + Working Directory CSV (`CALL GETOUTDIR`)  
