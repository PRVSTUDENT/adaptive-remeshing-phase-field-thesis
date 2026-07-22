# H1 four-thread baseline closeout

Classification: `h1_four_thread_reference_qualified`

## vs serial H1

- peak RF rel: 0.0
- prepeak NRMSE: 6.066904601837708e-11
- u_peak_ok: True

## Fair cost (both 4 threads)

| Quantity | H1 4-thr | Refined-v3 4-thr | Reduction |
| --- | ---: | ---: | ---: |
| Elements | 12064 | 10290 | 14.7% |
| Walltime s | 1195 | 995 | 16.7% |
| CPU s | 3553 | 3022 | 14.9% |
| Mem kB | 770996.0 | 599968 | 22.2% |

Both use cpus=4 mp_mode=threads. Do not attribute all differences solely to remeshing; confirm modules/hardware class/output controls match.

