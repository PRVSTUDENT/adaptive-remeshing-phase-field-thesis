# P3-SM1TC corrected thread-ID serial result

Job `1378240.mmaster02` passed as
`stage_p3sm1tc_thread_id_serial_pass`. The installed documented
`get_thread_id()` interface completed three controlled UEL invocations and
returned zero each time under one MPI rank and one OpenMP thread.

- scheduler/solver exit: 0/0
- before/after: 3/3; unmatched: 0
- returned IDs: [0, 0, 0]; unique IDs: [0]
- signal 11 and unresolved symbols: absent
- all four P3-SM0 callback categories: observed
- state coverage: 32/32
- RF rows: 11
- energy rows: 11
- increment records: 13
- completion marker: present
- retry: none
- P3-SM1R and P3-T4 remain blocked pending a separate route decision
