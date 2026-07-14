@echo off
setlocal

set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS2022INSTALLDIR%\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" intel64

where ifx
where link
where abaqus
ifx --version

cd /d "D:\Master thesis\Adaptive remeshing\runs\molnar_single_notch_unchanged\20260714_technical_gate_local\work"
abaqus job=SingleNotch input=SingleNotch.inp user=SingleNotch.for cpus=1 interactive
