@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" >nul 2>&1
cd /d "D:\Master thesis\Adaptive remeshing"
py -3 models\pandey_kumar_mode1\293_method_c_case5\case5_single_job_orchestrator.py %*
