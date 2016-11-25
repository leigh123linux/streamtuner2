@set installFolder=Do_Not_Change
@set usrFolder=Do_Not_Change
@set Python=Do_Not_Change
@echo off
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

echo Please wait, checking access permission...
echo.
netstat /b >nul
if errorlevel 1 (
	color 0C
	prompt $
	echo You must run the uninstall with administrative privileges
	pause
	exit
)

:skipnetstat
if NOT "%cd%" == "%TEMP%" (
	copy "%UsrFolder%\share\streamtuner2\dev\uninstall.cmd" "%temp%" 1>nul 2>&1
	"%temp%\uninstall.cmd"
)

echo This will uninstall Streamtuner2
echo.
echo Do you want to keep your Streamtuner2 settings? (y/n)

set INPUT=
set /P INPUT= %=%
If /I %INPUT%==N (
	echo Deleting personal settings...
	del "%Userprofile%\AppData\Roaming\streamtuner2\*.*" /F /S /Q
)
 
echo Do you want to uninstall Python? (y/n)
set INPUT=
set /P INPUT= %=%
If /I %INPUT%==Y (
	echo Removing LXML
	"%Python%\Removelxml.exe" -u "C:\Python27\lxml-wininst.log"
	echo Removing PIL
	"%Python%\RemovePIL.exe" -u "C:\Python27\PIL-wininst.log"
	echo Removing requests
	"%Python%\scripts\pip.exe" uninstall requests -q <"%UsrFolder%\share\streamtuner2\dev\Y" 1>nul
	echo Removing pyquery
	"%Python%\scripts\pip.exe" uninstall pyquery -q <"%UsrFolder%\share\streamtuner2\dev\Y" 1>nul
	echo Removing cssselect
	"%Python%\scripts\pip.exe" uninstall cssselect -q <"%UsrFolder%\share\streamtuner2\dev\Y" 1>nul
	echo Removing PyGtk
	MsiExec.exe /x{09F82967-D26B-48AC-830E-33191EC177C8} /qb-!
	echo Removing Python 27
	MsiExec.exe /x{9DA28CE5-0AA5-429E-86D8-686ED898C665} /qb-!
	rd %Python%  /S /Q
)

echo Removing Streamtuner2
rd "%installFolder%" /S /Q

echo Removing shortcuts
rd "%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Streamtuner2" /S /Q
del "%USERPROFILE%\Desktop\Streamtuner2.lnk" 1>nul

reg delete HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Streamtuner2 /f 1>nul

echo Finished uninstalling Streamtuner2
pause
