# Stage F19 rollback flag-I/O decision

F19 replaces F18 absence-based behavior with two required, wrapper-created files: `<JOBNAME>_f19_force_mode.flag` and `<JOBNAME>_f19_cutback_state.flag`. Each contains exactly integer 0 or 1 plus a final LF. The shared UEL source uses `INQUIRE` before every flag `OPEN` and checks `IOSTAT` for every `INQUIRE`, `OPEN`, `READ`, `WRITE`, and `CLOSE`. Missing or invalid files emit a controlled diagnostic and terminate through `XIT`; they cannot cause an unhandled Intel runtime abort.

Control creates mode/state `0/0`; forced creates `1/0`. Before the sole allowed `PNEWDT=0.5` return, the UEL persists state 1 outside SVARS. A retry rereads state 1 and cannot deliberately request another cutback. Control and forced source, deck, extractor, analyzer, and harness are byte-identical.
