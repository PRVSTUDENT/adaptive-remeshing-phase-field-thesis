# P3-SM1T isolated GETTHREADID serial result

Job `1378239.mmaster02` is classified as
`stage_p3sm1t_threadid_serial_fail_identifier`. Abaqus compiled and linked
the user source and completed input processing. At the controlled UEL call,
the before marker was written and dynamic resolution failed with
`libstandardU.so: undefined symbol: getthreadid_`. The after marker was not
written. This is an identifier-utility/interface result, not a thread-safety
result.

- before/after: 1/0; unmatched: 1
- returned IDs: none; unique IDs: none
- last marker: `P3SM1T_BEFORE_GETTHREADID`
- signal 11: false
- scheduler/solver exit: 10/1
- retry: none and unauthorized
- scratch ODB: metadata only; not copied into the repository
- P3-SM1R and all downstream lanes remain blocked
