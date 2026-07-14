# Molnar and Gravouil 2017 Original Supplement

Status: preserved original supplementary files. Do not edit files in this folder.

Source article:

- Gergely Molnar and Anthony Gravouil, "2D and 3D Abaqus implementation of a robust staggered phase-field solution for modeling brittle fracture", Finite Elements in Analysis and Design 130 (2017) 27-38.
- DOI: `10.1016/j.finel.2017.03.002`
- Article page: `https://www.sciencedirect.com/science/article/abs/pii/S0168874X16304954`
- Supplement archive URL used: `https://ars.els-cdn.com/content/image/1-s2.0-S0168874X16304954-mmc1.zip`

The downloaded archive is preserved locally under `tmp/downloads/` and remains ignored by Git. The extracted `.for` and `.inp` files below are tracked as the unmodified baseline source/deck copies for reproducibility.

## Archive Checksum

| Archive | Bytes | SHA-256 |
|---|---:|---|
| `tmp/downloads/molnar_2017_mmc1_candidate.zip` | 565601 | `7e210cf5ead1cbf197cc5b9180475d1537e4d84264b8b655b1b5cc426657a400` |

## Preserved Files

| File | Bytes | SHA-256 |
|---|---:|---|
| `models/baseline_original/molnar_gravouil_2017/01_One_Element/OneElement.for` | 19964 | `8688a21a987a0348f4211cb90e365a60902dce922294a915a48644c8dae067e2` |
| `models/baseline_original/molnar_gravouil_2017/01_One_Element/OneElement.inp` | 4254 | `9b63615bbe335872de197b96ca0253769f4a237c1e2e384294a1d204c462f220` |
| `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for` | 19970 | `18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1` |
| `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp` | 504303 | `89ce3f32e396b0e484be6753a272dd6bbb2a2f9daff426d6a57419f57d665b72` |
| `models/baseline_original/molnar_gravouil_2017/03_Double_Notch_Tension/DoubleNotch.for` | 19972 | `8cefde64ef7ff5e26986d2794f433cf827ee75ef88595330eb65d6d8b9155be6` |
| `models/baseline_original/molnar_gravouil_2017/03_Double_Notch_Tension/DoubleNotch.inp` | 1387058 | `cbfa82a1145c1bf409ec6cd65fe3be002ceed8ff474cd134d4b090f7d9c9f857` |
| `models/baseline_original/molnar_gravouil_2017/04_One_Element_3D/OneElement3D.for` | 24894 | `b4afe7165a20c53894a57b7d3e0d838050c2a6917ea3734e6c949dd155da3604` |
| `models/baseline_original/molnar_gravouil_2017/04_One_Element_3D/OneElement3D.inp` | 4308 | `7d0248444259864d0d7ba66454204be6264f85bed07cc2bc13dfe6a76f12e708` |

## Next Gate

Run a minimal Abaqus user-subroutine compiler/linker smoke test before running these examples or modifying any source file.
