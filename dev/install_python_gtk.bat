@echo off
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
echo ^|    Installer for Python 2.7.12 ^& Gtk 2.24.2                                 ^|
echo  ----------------------------------------------------------------------------- 
echo.
PowerShell.exe -Command "& {Start-Process Powershell.exe -ArgumentList '-ExecutionPolicy ByPass -File ""%~dpn0.ps1""' -Verb RunAs}" 
