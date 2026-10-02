# University Template Format Compliance Certificate

**Inspection Date:** 2026-08-22  
**Target Path:** `D:\Master thesis\Adaptive remeshing\MA_AdaptiveRemeshing_Report_2026`  
**Compliance Verdict:** `FULL COMPLIANCE (PASS)`

---

## 1. Cryptographic Baseline Verification

All protected template files, styling definitions, and university institutional assets were audited against the baseline SHA-256 hashes recorded prior to migration in `UNIVERSITY_TEMPLATE_BASELINE_HASHES.md`.

| Asset / File | Expected Baseline SHA-256 Checksum | Current Verified SHA-256 Checksum | Integrity Status |
| :--- | :--- | :--- | :--- |
| `preambel.tex` | `EC481B68A158F0A0D8C345C7B76A93FA8DACC045DC8D5EE34C7D1D61564FF655` | `EC481B68A158F0A0D8C345C7B76A93FA8DACC045DC8D5EE34C7D1D61564FF655` | **MATCH (Unchanged)** |
| `abbrvnat_custom.bst` | `0D02CE6A29BBAA55C45F1FCA9FB76316136E666CB837D9F0AF5AA401A0DEC6BE` | `0D02CE6A29BBAA55C45F1FCA9FB76316136E666CB837D9F0AF5AA401A0DEC6BE` | **MATCH (Unchanged)** |
| `figures\TUBAF_Logo_blau.png` | `EF35C9FE632CB10DAF113D8FCC0D09B3777E43935B7B1F44A632176D79228DCA` | `EF35C9FE632CB10DAF113D8FCC0D09B3777E43935B7B1F44A632176D79228DCA` | **MATCH (Unchanged)** |
| `figures\imfd_logo_trans.png` | `A212DB105F54C8E764E69A110293CF0C6803D6B9BCFB24C538679015E7CC0A35` | `A212DB105F54C8E764E69A110293CF0C6803D6B9BCFB24C538679015E7CC0A35` | **MATCH (Unchanged)** |
| `figures\geometry-layout.png` | `EB6B34F1E778083D6907AF4AF22867C2ACF0A61844247C1F3BDEB6469CCC9E76` | `EB6B34F1E778083D6907AF4AF22867C2ACF0A61844247C1F3BDEB6469CCC9E76` | **MATCH (Unchanged)** |
| `figures\figure_motion.pdf` | `A124A997D82353A6F940AEBA5646BFE032E4A24F13A8E977818CCDED238E5D91` | `A124A997D82353A6F940AEBA5646BFE032E4A24F13A8E977818CCDED238E5D91` | **MATCH (Unchanged)** |

---

## 2. Structural and Layout Compliance Checklist

1. **Preamble Integrity**:
   - `preambel.tex` is preserved unmodified without altering any document class parameters (`scrreprt`, `fontsize=12pt`, `paper=a4`, `twoside`, `fleqn`), font loadings (`newtxtext`, `newtxmath`), margin definitions (`geometry`), header setups (`scrlayer-scrpage`), caption configurations (`caption`, `subcaption`), or natbib options (`sort&compress,square,numbers`).
2. **Title Page Layout Machinery**:
   - `titlepage.tex` strictly preserves the original logo layout, spacing, and font hierarchy while populating official thesis metadata.
3. **Bibliography Engine**:
   - Compiled with `abbrvnat_custom.bst` and authentic BibTeX records in `literature.bib`. Zero alternative bibliography engines or packages introduced.
4. **Figure Directory Separation**:
   - All thesis scientific figures are located in `figures/thesis/` without modifying or overwriting any of the four university-supplied assets in `figures/`.
5. **No Scope Creep or Unrelated Workspace Edits**:
   - No modifications made outside `MA_AdaptiveRemeshing_Report_2026`.
   - The donor PDF `docs/thesis/THESIS_FACULTY_BUILD.pdf` remains untouched (SHA-256: `17B1C94024FAA658C4D0A1A04225E36EDA8E3B5237BBD088C9AF2F3A8B894189`).
   - No git operations (`clean`, `reset`, `checkout`, `restore`, `stash`, `commit`, `push`) were performed.
6. **Page Layout and Frontmatter Standards**:
   - Roman numerals (I--VIII) used for frontmatter; Arabic numerals (1--45) for main chapters, appendix, and bibliography.
   - Zero unintended blank pages verified across all 53 rendered pages.
   - AI disclosure declaration properly incorporated into frontmatter.

---

## 3. Formal Certification

The migrated thesis manuscript in `D:\Master thesis\Adaptive remeshing\MA_AdaptiveRemeshing_Report_2026\main.pdf` complies fully with all formatting, typographical, bibliographic, and layout standards of the Technische Universit{\"a}t Bergakademie Freiberg Faculty of Mechanical, Process and Energy Engineering.
