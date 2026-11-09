@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Task F1698 Experiment 1: Running All 15 Patch Jobs
echo ===================================================

call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" intel64

cd /d "D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\198_pk_sec43_coupled_validation"

set JOBS=PATCH_A_INTACT PATCH_A_PARTIAL PATCH_A_STRONG PATCH_B1_INTACT PATCH_B1_PARTIAL PATCH_B1_STRONG PATCH_B2_INTACT PATCH_B2_PARTIAL PATCH_B2_STRONG PATCH_B3_INTACT PATCH_B3_PARTIAL PATCH_B3_STRONG PATCH_C_INTACT PATCH_C_PARTIAL PATCH_C_STRONG

for %%J in (%JOBS%) do (
    echo.
    echo ---------------------------------------------------
    echo Starting Job: %%J
    echo ---------------------------------------------------
    if exist "%%J.lck" del /f /q "%%J.lck"
    call abaqus job=%%J user=f1698_patch_uel.for interactive
    echo Finished %%J with exit code !ERRORLEVEL!
)

echo.
echo ===================================================
echo All 15 patch jobs finished. Extracting results...
echo ===================================================
call abaqus python "..\..\..\scripts\extract_patch_validation_results.py"

echo Execution and extraction complete.
