@echo off
cls
PowerShell Set-ExecutionPolicy -ExecutionPolicy ByPass -Scope CurrentUser
PowerShell -File \usr\share\streamtuner2\dev\install_python_gtk.ps1
PowerShell Set-ExecutionPolicy -ExecutionPolicy Undefined -Scope CurrentUser
