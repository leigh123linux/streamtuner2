@set installFolder=Do_not_change
@set usrFolder=Do_not_change
@set Python=Do_not_change
@set StreamripperFolder=Do_not_change
@echo off

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
	copy "%UsrFolder%\share\streamtuner2\dev\uninstall.cmd" "%temp%\STuninst.cmd" 
	"%temp%\STuninst.cmd"
)

echo | set /p=Do you want to uninstall Streamtuner2 for Windows? [y/N]
set /P INPUT=%=%
If /I NOT '%INPUT%' == 'Y' exit

echo | set /p=Do you want to keep your Streamtuner2 settings? [Y/n]
set /P INPUT=%=%
If /I '%INPUT%' == 'N' (
	echo Deleting personal settings...
	del "%Userprofile%\AppData\Roaming\streamtuner2\*.*" /F /S /Q
)
set INPUT=

if '"%StreamripperFolder%"' NEQ '' ( 
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
 	reg delete HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Streamripper /f 1>nul 2>&1
 	reg delete HKLM\SOFTWARE\WoW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Streamripper /f 1>nul 2>&1
)
set INPUT=

:uninstallPython
echo | set /p=Do you want to keep your Python 2.7.12 installation? [Y/n]
set /P INPUT=%=%
If /I '%INPUT%' == 'N' (
	echo Removing PIL 1.1.7
	"%Python%\RemovePIL.exe" -u "%Python%\PIL-wininst.log"
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
	echo Removing Python 2.7.12
	MsiExec.exe /x{9DA28CE5-0AA5-429E-86D8-686ED898C665} /qb-!
	reg delete HKCU\SOFTWARE\Python\PythonCore\2.7 /f 1>nul 2>&1
	rd "%Python%"  /S /Q
)

echo Removing Streamtuner2
rd "%installFolder%" /S /Q

echo Removing shortcuts
rd "%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Streamtuner2" /S /Q
del "%USERPROFILE%\Desktop\Streamtuner2.lnk" 1>nul

reg delete HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Streamtuner2 /f 1>nul  2>&1

echo Finished uninstalling Streamtuner2
pause
