@set installFolder=Do_not_Change
@set Python=Do_not_Change
@set StreamripperFolder=Do_not_Change
@echo off
set ST2=Streamtuner2

>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if '%errorlevel%' NEQ '0' (
    goto goUAC
)	  else goto goADMIN

:goUAC
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:goADMIN
    pushd "%CD%"
    CD /D "%~dp0"
cls
echo  -----------------------------------------------------------------------------
echo ^|                                                                             ^|
echo ^|       _____/\\\\\\\\\\\____/\\\\\\\\\\\\\\\____/\\\\\\\\\_____              ^|
echo ^|        ___/\\\/////////\\\_\///////\\\/////___/\\\///////\\\___             ^|
echo ^|         __\//\\\______\///________\/\\\_______\///______\//\\\__            ^|
echo ^|          ___\////\\\_______________\/\\\_________________/\\\/___           ^|
echo ^|           ______\////\\\____________\/\\\______________/\\\//_____          ^|
echo ^|            _________\////\\\_________\/\\\___________/\\\//________         ^|
echo ^|             __/\\\______\//\\\________\/\\\_________/\\\/___________        ^|
echo ^|              _\///\\\\\\\\\\\/_________\/\\\________/\\\\\\\\\\\\\\\_       ^|
echo ^|               ___\///////////___________\///________\///////////////__      ^|
echo ^|                                                                             ^|
echo ^|    Streamtuner2 for Windows                               Version 2.2.0     ^|
echo ^|                                                                             ^|
echo ^|    Uninstall                                                                ^|
echo  ----------------------------------------------------------------------------- 
echo.
echo.

setlocal enableextensions
cd /d "%~dp0"

if NOT "%cd%" == "%TEMP%" (
	copy "%installFolder%\usr\share\streamtuner2\dev\uninstall.cmd" "%temp%\STuninst.cmd" 
	"%temp%\STuninst.cmd"
)

tasklist /fi "Imagename eq python.exe" /fi "Windowtitle eq %ST2%*" /v | find "%ST2%" >nul
if %errorlevel% EQU 0 goto ST2isRunning
tasklist /fi "Imagename eq pythonw.exe" /fi "Windowtitle eq %ST2%*" /v | find "%ST2%" >nul
if %errorlevel% EQU 0 goto ST2isRunning
tasklist /fi "Imagename eq python.exe" | find "python.exe" >nul
if %errorlevel% EQU 1 goto NotRunning
echo.
echo There's a Python process running.
echo Please close all instances of Python before uninstalling!
set Pythonrun=Y
pause
goto NotRunning

:ST2isRunning
echo %ST2% is still running!
echo Please close all instances of %ST2% before uninstalling!
pause
exit


:NotRunning
if exist "%windir%\SysWOW64" (
	set RegUninstallBase="HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
) else (
	set RegUninstallBase="HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall"
)

echo | set /p=Do you want to uninstall %ST2% for Windows? [y/N]
set /P INPUT=%=%
If /I NOT '%INPUT%' == 'Y' exit

echo | set /p=Do you want to keep your %ST2% settings? [Y/n]
set /P INPUT=%=%
If /I '%INPUT%' == 'N' (
	echo Deleting personal settings...
	rd "%APPDATA%\streamtuner2" /S /Q 1>nul 
	rem del "%APPDATA%\streamtuner2\*.*" /F /S /Q 1>nul
)
set INPUT=

if '"%StreamripperFolder%"' NEQ '""' ( 
	echo | set /p=Do you want to uninstall Streamripper? [y/N]
	goto uninstallSR
)
goto uninstallPython

:uninstallSR
set /P INPUT=%=%
If /I '%INPUT%' == 'Y'  (
	echo Uninstalling Streamripper...
	"%StreamripperFolder%\Uninstall.exe" /S
 	reg delete HKCU\SOFTWARE\Streamripper /f 1>nul 2>&1
 	reg delete %RegUninstallBase%\Streamripper /f 1>nul 2>&1
)
set INPUT=

:uninstallPython
if '%Pythonrun%' EQU 'Y' (
	echo Skipping uninstall of Python
	goto uninstallST2
)
echo | set /p=Do you want to keep your Python 2.7.13 installation? [Y/n]
set /P INPUT=%=%
If /I '%INPUT%' == 'N' (
	echo Uninstalling Python...
	echo Removing PIL 1.1.7
	"%Python%\RemovePIL.exe" -u "%Python%\PIL-wininst.log"
	if exist "%Python%\Lib\site-packages\mutagen-1*py2.7.egg-info" (
		echo Removing Mutagen
		"%Python%\scripts\pip.exe" uninstall mutagen -y -q
	)
	echo Removing pyquery 1.2.17
	"%Python%\scripts\pip.exe" uninstall pyquery -y -q
	echo Removing LXML 2.3
	"%Python%\scripts\pip.exe" uninstall lxml -y -q
	echo Removing requests
	"%Python%\scripts\pip.exe" uninstall requests -y -q
	echo Removing cssselect
	"%Python%\scripts\pip.exe" uninstall cssselect -y -q
	echo Removing PyGtk 2.24.2
	MsiExec.exe /x{09F82967-D26B-48AC-830E-33191EC177C8} /qb-!
	reg delete %RegUninstallBase%\{09F82967-D26B-48AC-830E-33191EC177C8} /f 1>nul 2>&1
	echo Removing Python 2.7.13
	MsiExec.exe /x{4A656C6C-D24A-473F-9747-3A8D00907A03} /qb-!
	reg delete HKCU\SOFTWARE\Python\PythonCore\2.7 /f 1>nul 2>&1
	reg delete %RegUninstallBase%\{4A656C6C-D24A-473F-9747-3A8D00907A03} /f 1>nul 2>&1
	rd "%Python%"  /S /Q
	echo Removing installed Gtk2-Themes
	rd "%APPDATA%\streamtuner2\themes" /S /Q
)

:uninstallST2 
echo Removing %ST2%...
rd "%installFolder%" /S /Q

echo Removing shortcuts...
rd "%APPDATA%\Microsoft\Windows\Start Menu\Programs\%ST2%" /S /Q 1>nul
del "%USERPROFILE%\Desktop\Streamtuner2.lnk" 1>nul

reg delete HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%ST2% /f 1>nul  2>&1

echo Finished uninstalling %ST2%
pause
