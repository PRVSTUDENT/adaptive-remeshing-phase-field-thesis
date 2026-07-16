# SDV15 Irreversibility Audit

Classification: `sdv15_review_required`

The ODB scan reports `6113` SDV15 decreases using tolerance `1e-08` and ODB precision tolerance `1e-06`. The worst decrease is `0.000425219535828` at element `84131`, integration point `3`, between global frames `189` and `190`.

The maximum SDV15 value is `1.005600095`. First overshoot above 1 occurs at `U2 = 0.006330000 mm`; the maximum overshoot is `0.005600095` at `U2 = 0.006500000 mm`.

Decrease categories:

- Smaller than ODB precision: `4816`
- Same-location consecutive frames: `6113`
- Staggered sync candidates: `1764`
- Genuine healing candidates: `817`

Interpretation: SDV15 is not cleanly monotone under the current extracted tolerance, and its late overshoot/decrease behavior remains a scientific-review issue. It is not a technical execution failure.
