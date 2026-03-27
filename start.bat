@echo off
chcp 65001 >nul 2>&1
title OSM Kleinort-Extraktor

echo.
echo  +======================================+
echo  ^|     OSM Kleinort-Extraktor           ^|
echo  ^|     Starte Umgebung...               ^|
echo  +======================================+
echo.

REM --- Conda-Root bestimmen ---
set CONDA_ROOT=

if exist "C:\ProgramData\miniconda3\Scripts\conda.exe" (
    set CONDA_ROOT=C:\ProgramData\miniconda3
    goto :conda_gefunden
)
if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
    set CONDA_ROOT=%USERPROFILE%\miniconda3
    goto :conda_gefunden
)
if exist "%USERPROFILE%\Miniconda3\Scripts\conda.exe" (
    set CONDA_ROOT=%USERPROFILE%\Miniconda3
    goto :conda_gefunden
)
if exist "%LOCALAPPDATA%\miniconda3\Scripts\conda.exe" (
    set CONDA_ROOT=%LOCALAPPDATA%\miniconda3
    goto :conda_gefunden
)
if exist "%USERPROFILE%\anaconda3\Scripts\conda.exe" (
    set CONDA_ROOT=%USERPROFILE%\anaconda3
    goto :conda_gefunden
)

echo FEHLER: Miniconda/Anaconda nicht gefunden.
echo Bitte installieren: https://docs.conda.io
pause
exit /b 1

:conda_gefunden
echo Conda gefunden: %CONDA_ROOT%
echo.

REM --- Conda-Hook laden und base aktivieren ---
call "%CONDA_ROOT%\Scripts\activate.bat" base
if %errorlevel% neq 0 (
    echo FEHLER: Conda-Aktivierung fehlgeschlagen.
    pause
    exit /b 1
)

REM --- osmium pruefen ---
where osmium >nul 2>&1
if %errorlevel% neq 0 (
    echo HINWEIS: osmium nicht im PATH - wird automatisch im Conda-Verzeichnis gesucht.
    echo Falls noetig: conda install -c conda-forge osmium-tool
    echo.
)

REM --- Conda-Python direkt aufrufen (nicht das System-Python im PATH) ---
set SCRIPT_DIR=%~dp0
set CONDA_ROOT_FOR_PYTHON=%CONDA_ROOT%
"%CONDA_ROOT%\python.exe" "%SCRIPT_DIR%main.py"

if %errorlevel% neq 0 (
    echo.
    echo FEHLER: Programm mit Fehlercode %errorlevel% beendet.
    pause
)
