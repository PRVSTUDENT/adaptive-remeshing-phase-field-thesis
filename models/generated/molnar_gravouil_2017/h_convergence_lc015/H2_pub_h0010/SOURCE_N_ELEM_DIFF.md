# Source diff proof for H2_pub_h0010
# Only permitted change: N_ELEM value
# preserved: N_ELEM=3930
# generated: N_ELEM=33852

--- SingleNotch.for (preserved)
+++ H2_pub_h0010.for
@@
-      PARAMETER(... N_ELEM=3930, ...)
+      PARAMETER(... N_ELEM=33852, ...)
-      COMMON/KUSER/USRVAR(N_ELEM=3930, ...)
+      COMMON/KUSER/USRVAR(N_ELEM=33852, ...)

Note: both PARAMETER and COMMON uses of N_ELEM are updated by the same
token replacement; no residual/tangent/history/formulation logic changes.
