# Stage F11 prior-converged-state contract

`PHASEOLD` is loaded from the phase UEL `SVARS` array before the current call
writes updated `SVARS`. Abaqus/Standard supplies state variables at the start
of an increment and commits their updated values only for an accepted
increment; rejected increments restore the start-of-increment values.

F11 records a bounded call-level audit for element 1, integration point 1,
including step, increment, times, increment size, iteration surrogate,
received `PHASEOLD`, start-of-increment trial phase, current phase, and gap.
The candidate preflight requires this load-before-write structure and the
bounded log. Runtime interpretation requires the received value to stay fixed
through calls in an increment and advance only after acceptance. A cutback,
if one occurs, must restore the same prior value; absence of a cutback is
reported as “not exercised,” not claimed as an experimental cutback pass.
