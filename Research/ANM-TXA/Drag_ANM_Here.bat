@echo off
REM ANM to TXA Converter - Drag and Drop
REM Drag ANM files onto this batch file to convert them silently

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Get the full path to the exe
set "EXE_PATH=%SCRIPT_DIR%dist\ANM_to_TXA_Converter.exe"

REM Check if exe exists
if not exist "%EXE_PATH%" (
    echo.
    echo ERROR: ANM_to_TXA_Converter.exe not found at:
    echo %EXE_PATH%
    echo.
    echo Please ensure the exe is in the dist folder.
    echo.
    pause
    exit /b 1
)

REM Convert all dropped files
if "%~1"=="" (
    echo.
    echo ANM to TXA Converter
    echo Drag ANM files onto this batch file to convert them
    echo.
    pause
) else (
    REM Convert each dropped file silently
    :convert_next
    if not "%~1"=="" (
        "%EXE_PATH%" "%~1"
        shift
        goto convert_next
    )
    echo.
    echo Conversion complete!
    pause
)

endlocal

