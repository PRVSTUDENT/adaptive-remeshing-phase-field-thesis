# D3A Checkpoint Extraction Attempt History

## 1376868.mmaster02

Classification: `stage_d3a_extractor_fail_frame_index`

The first CAE/ODB-only extraction attempt failed before validation because the extractor used Abaqus `frameId` as a Python frame-list index.

## 1376877.mmaster02

Classification: `stage_d3a_extractor_fail_csv_extra_fields`

The second CAE/ODB-only extraction attempt wrote state CSVs but failed while writing `D3_CHECKPOINT_RF_U.csv` because Abaqus Python 2.7 `csv.DictWriter` rejected extra candidate fields.

## 1376879.mmaster02

Classification: `stage_d3a_checkpoint_fail_missing_energy_history`

The corrected extractor produced the checkpoint state package and selected the exact target frame near `U2=0.003 mm`, but validation failed because the source ODB does not contain `ALLIE`, `ALLSE`, or `ALLWK` energy history outputs. No `D3A.ok` marker was written.

No Abaqus/Standard solve or UEL compilation was performed in any attempt.
