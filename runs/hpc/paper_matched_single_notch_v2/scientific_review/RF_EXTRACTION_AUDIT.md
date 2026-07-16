# RF Extraction Audit

Classification: `rf_extraction_audit_pass_with_scope_limit`

This audit uses the committed extracted curve and the candidate deck. It does not run Abaqus/Standard or submit PBS. The ODB-side extraction was already performed read-only during the technical pass postprocessing.

## Findings

- RP node set contains one node: `34508` at `(0.0, 0.5)`.
- The deck ties the top boundary vertical displacement to RP DOF 2 through `*Equation`.
- Both steps request `RF, U` on `nset=RP`.
- Extracted curve rows: `202`.
- U2 is monotone non-decreasing: `True`.
- Duplicate U2 rows: `1`.
- Peak RF2: `0.761702 kN` at `U2 = 0.006110 mm`.
- Final RF2: `0.749110 kN` at `U2 = 0.006700 mm`.

## Scope Limit

The local evidence verifies the deck/output path and the extracted series consistency. A byte-for-byte independent ODB re-extraction would require another read-only Abaqus Python pass on the scratch ODB; no such pass was needed for this local forensic package because the committed extractor outputs are internally consistent and traceable to RP output requests.
