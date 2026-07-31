# Stage F10 corrected minimal baseline

Job `1380091.mmaster02` completed the Abaqus analysis with the corrected
compact mapping: phase UEL 1--23, displacement UEL 24--46, and CPE4 overlay
47--69. No COMMON-array guard fired.

Across 102 frames, the baseline had four negative fixed-point phase changes;
the minimum was `-5.78165054321289e-06`. SDV16 was monotone. Phase ranged
from 0 to 1.00007653236389. The initial stiffness was 78.8781862783439,
peak RF1 was 0.0347024991060607, and final RF1 was
0.00019242075791225943 at U1 0.006000000052154064. The solve used 100
increments, 118 total iterations, and zero cutbacks.

The ODB extraction wrote the three CSV files before its summary step failed
because Abaqus Python 2.7 lacks `math.isfinite`. More importantly, the deck
requested energy as field output, which Abaqus reported unavailable, so the
required energy consistency evidence does not exist.
