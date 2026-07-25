# Thesis LaTeX Build Record

Classification: `wp7_final_latex_build_pass`

Final WP7-F1 build date: 2026-07-25

Entry point:
`docs/thesis/THESIS_CLOSEOUT_BUILD.tex`

Successful compiler: bundled Tectonic 0.16.9

Output:
local temporary review directory outside the repository

Result: 30-page PDF generated successfully. The increase from the earlier
28-page closeout build is the now-included frozen Stage-P parallelization
subsection.

The two new standalone Stage-B reports also compiled successfully:

- `STAGE_B_RESULTS_REPORT.tex`: 3 pages;
- `STAGE_B_EXECUTION_AND_FAILURE_LOG.tex`: 3 pages.

The initial local MiKTeX/latexmk attempt failed because that installation was
missing `grfext.sty` and reported out-of-sync user/administrator packages.
The supported Tectonic fallback then identified a pre-existing math-mode error
in `STAGE_D_STATE_TRANSFER_CHAPTER.tex`. After that source error was corrected,
Tectonic completed successfully. Remaining messages are layout warnings for
long identifiers and tables, not missing references or fatal errors.

Build command:

```text
python <latex-plugin>/scripts/compile_latex.py
  docs/thesis/THESIS_CLOSEOUT_BUILD.tex
  --compiler tectonic
  --output-directory results/latex_build_stage_e
  --json
```

The final build emitted only nonfatal layout warnings for long hashes,
identifiers, paths, and narrow tables. There were no missing inputs,
references, or fatal errors.

Generated PDFs remain local review artifacts outside Git. The TeX entry point,
the Stage-B TeX sources, `results/final/WP7_LATEX_BUILD_GATE.txt`, and this
record are the committed reproducibility evidence.
