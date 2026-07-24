# Thesis LaTeX Build Record

Classification: `THESIS_LATEX_BUILD_PASS`

Entry point:
`docs/thesis/THESIS_CLOSEOUT_BUILD.tex`

Successful compiler: bundled Tectonic 0.16.9

Output:
`results/latex_build_stage_e/THESIS_CLOSEOUT_BUILD.pdf`

Result: 28-page PDF generated successfully.

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

The generated PDF is a local review artifact; the TeX entry point and this
record are the reproducibility evidence.
