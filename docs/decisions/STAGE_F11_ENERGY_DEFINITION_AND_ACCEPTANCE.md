# Stage F11 diagnostic energy definition and acceptance

The custom UEL does not provide a complete Abaqus global variational-energy
contract. Its displacement branch assigns `ENERGY(2)` to an unintegrated
integration-point value, while the history-field phase equation is not the
Euler equation of one exact recoverable global potential. Consequently F11
uses a **diagnostic balance**, not a claim of exact energy conservation.

With force in kN, displacement in mm, stress in kN/mm², volume in mm³ and
energy in kN·mm:

- external work is trapezoidal integration
  `Wext[n]=Wext[n-1]+0.5*(RF[n]+RF[n-1])*(U[n]-U[n-1])`;
- degraded elastic energy is
  `∫ 0.5*((1-d)^2+k)*(sigma:epsilon) dV`;
- crack energy is
  `∫ [Gc/(2*lc)*d^2 + Gc*lc/2*|grad d|^2] dV`;
- the history-driven term is reported separately as
  `∫ H*(1-d)^2 dV` and is not labelled recoverable energy;
- penalty energy is
  `∫ 0.5*beta*<d_old-d>_+^2 dV`;
- total diagnostic energy is elastic plus crack plus penalty energy;
- incremental diagnostic imbalance is the increment of total diagnostic
  energy minus the increment of external work.

Predeclared acceptance policy:

- all energy terms finite;
- penalty energy nonnegative;
- baseline penalty quantities exactly zero;
- no unexplained positive cumulative diagnostic imbalance exceeding the
  larger of `1e-8 kN mm` and 2% of maximum absolute external work;
- initial stiffness relative difference at most `1e-6`;
- maximum RF-curve difference at most `1e-4` of the common peak;
- no fixed-point phase decrease below `-1e-7`;
- phase range `[-1e-7, 1+1e-4]`;
- candidate iterations at most 25% above baseline and no additional cutback.
