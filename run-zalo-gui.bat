@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

set "PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%"

if exist "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" (
    start "" /b "%SCRIPT_DIR%.venv\Scripts\pythonw.exe" -m browser_automation.interfaces.gui.zalo_app
    goto :success
)

if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    start "" /b "%SCRIPT_DIR%.venv\Scripts\python.exe" -m browser_automation.interfaces.gui.zalo_app
    goto :success
)

where pyw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" /b pyw -3 -m browser_automation.interfaces.gui.zalo_app
    goto :success
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" /b py -3 -m browser_automation.interfaces.gui.zalo_app
    goto :success
)

where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" /b pythonw -m browser_automation.interfaces.gui.zalo_app
    goto :success
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" /b python -m browser_automation.interfaces.gui.zalo_app
    goto :success
)

echo Could not find Python. Create .venv or install Python 3.11+ first.
popd >nul
exit /b 1

:success
popd >nul
exit /b 0
