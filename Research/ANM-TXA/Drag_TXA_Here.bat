@echo off
REM Drag-and-drop TXA files onto this BAT to convert them to ANM using txa_to_anm.py
setlocal
set SCRIPT_DIR=%~dp0
set PY=%SCRIPT_DIR%\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

if "%~1"=="" (
  echo Drag one or more .txa files onto this file to convert them.
  pause
  goto :eof
)

for %%F in (%*) do (
  if /I "%%~xF"==".txa" (
    echo Converting %%~fF ...
    "%PY%" "%SCRIPT_DIR%txa_to_anm.py" "%%~fF"
  ) else (
    echo Skipping %%~fF (not .txa)
  )
)

echo Done.
pause
