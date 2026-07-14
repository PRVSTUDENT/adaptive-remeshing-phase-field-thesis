set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS2022INSTALLDIR%\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" intel64
where ifx
where link
where abaqus
ifx --version
link /?
cd /d "D:\Master thesis\Adaptive remeshing\tests\abaqus_user_subroutine_smoke"
abaqus job=smoke_user_subroutine input=smoke_user_subroutine.inp user=smoke_uexternaldb.for cpus=1 interactive