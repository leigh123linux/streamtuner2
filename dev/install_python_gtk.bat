@setlocal enableextensions
@cd /d "%~dp0"
@echo off
cls
PowerShell Set-ExecutionPolicy -ExecutionPolicy ByPass -Scope CurrentUser
PowerShell -File install_python_gtk.ps1
PowerShell Set-ExecutionPolicy -ExecutionPolicy Undefined -Scope CurrentUser
pause