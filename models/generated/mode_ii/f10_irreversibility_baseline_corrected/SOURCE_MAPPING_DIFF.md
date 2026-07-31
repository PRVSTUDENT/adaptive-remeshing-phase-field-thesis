# Reduced-model source mapping

The frozen H2 source remains unchanged. This isolated minimal source changes
the model-specific mapping constant from `N_ELEM=33852` to `N_ELEM=23` in
both UEL and UMAT and adds fail-safe bounds guards before each branch can
access `USRVAR`.

This is a reduced-model mapping adaptation. It does not change the
constitutive law, phase-field weak form, degradation, history update,
material parameters, or fracture parameters.
