# Stage F12 medium-H1 preparation result

The canonical U1=0.020 H1 deck and source hashes are respectively
`19a5c60fa45f8533f9499c27da56f57faebd8e04b10d567f6edde80bc87baea4`
and `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead`.
Deck/source inspection confirms 12,064 physical elements and N_ELEM=12064.

The instrumented baseline and Stage F11 penalty candidate packages are frozen
under `models/generated/mode_ii/f12_h1_*`. Both have mapped COMMON bounds
guards and passed the new preparation tests. They remain
`prepared_not_authorized`. Because rollback was not exercised, the pair is
not ready for a separate execution authorization. No H1 datacheck or analysis
was performed.
