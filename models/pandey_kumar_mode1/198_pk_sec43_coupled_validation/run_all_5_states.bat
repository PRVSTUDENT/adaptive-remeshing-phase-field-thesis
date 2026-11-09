@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Task F1698 Experiment 3: Running All 5 Section 4.3 Recovery Jobs
echo ===================================================

cd /d "D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\198_pk_sec43_coupled_validation"

set JOBS=SEC43_STATE1_INIT SEC43_STATE2_HOLE_ARREST SEC43_STATE3_SEC_INIT SEC43_STATE4_SEC_MIDPROP SEC43_STATE5_TERMINAL

for %%J in (%JOBS%) do (
    echo.
    echo ---------------------------------------------------
    echo Starting Job: %%J
    echo ---------------------------------------------------
    if exist "%%J.lck" del /f /q "%%J.lck"
    call abaqus job=%%J interactive ask_delete=OFF
    echo Finished %%J with exit code !ERRORLEVEL!
)

echo.
echo ===================================================
echo All 5 Section 4.3 recovery jobs finished.
echo ===================================================
