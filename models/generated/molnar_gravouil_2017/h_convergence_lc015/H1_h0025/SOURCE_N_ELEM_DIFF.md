# Source diff proof for H1_h0025
# Only permitted change: N_ELEM value
# preserved: N_ELEM=3930
# generated: N_ELEM=12064

--- SingleNotch.for (preserved)
+++ H1_h0025.for
@@
-      PARAMETER(... N_ELEM=3930, ...)
+      PARAMETER(... N_ELEM=12064, ...)
-      COMMON/KUSER/USRVAR(N_ELEM=3930, ...)
+      COMMON/KUSER/USRVAR(N_ELEM=12064, ...)

Note: both PARAMETER and COMMON uses of N_ELEM are updated by the same
token replacement; no residual/tangent/history/formulation logic changes.
