@echo off
set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 exit /b %errorlevel%
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" intel64 >nul 2>&1
if errorlevel 1 exit /b %errorlevel%
cd /d "D:\Master thesis\Adaptive remeshing"
py -3 models\pandey_kumar_mode2\294_method_c_mode2\run_cycle1_recovery.py %*
exit /b %errorlevel%
