@echo off
set PrefsFolder=%APPDATA%\streamtuner2
set ST2=Streamtuner2
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
echo ^|    Reset personal preferences                                               ^|
echo  ----------------------------------------------------------------------------- 
echo.

dir %PrefsFolder%\*.* 1>nul 2>&1
if %errorlevel% EQU 1 goto EmptyDir
dir %PrefsFolder%\*.* |find " 0 Bytes" 1>nul 2>&1
if %errorlevel% EQU 1 goto Proceed
:EmptyDir
echo.
echo No files have been found in your personal folder!
echo.
pause
exit

:Proceed
tasklist /fi "Imagename eq python.exe" /fi "Windowtitle eq %ST2%*" /v | find "%ST2%" >nul
if %errorlevel% EQU 0 goto ST2isRunning
tasklist /fi "Imagename eq pythonw.exe" /fi "Windowtitle eq %ST2%*" /v | find "%ST2%" >nul
if %errorlevel% EQU 0 goto ST2isRunning
tasklist /fi "Imagename eq python.exe" | find "python.exe" >nul
if %errorlevel% EQU 1 goto NotRunning
echo.
echo There's a Python process running.
echo Please make sure it's not related to %ST2%. 
echo | set /p= Do you want to proceed? [y/N]
set /P INPUT=%=%
If /I NOT '%INPUT%' == 'Y' exit
goto NotRunning


:ST2isRunning
echo.
echo %ST2% is still running!
echo Please close all instances of %ST2% before resetting your preferences!
echo.
pause
exit

:NotRunning
echo Your personal files are in %PrefsFolder%
echo.
echo This will delete all settings of %ST2% and the cached files. 
echo If you want to save your bookmarks before, then quit now and come back later...
echo.
echo.
echo | set /p=Do you want to clear all settings of %ST2% now? [y/N]
set /P INPUT=%=%
If /I NOT '%INPUT%' == 'Y' exit

del %PrefsFolder%\*.*  /F /S /Q 1>nul
rd %PrefsFolder% /S /Q 
echo.
echo.
echo Your %ST2% settings have been deleted.
pause
