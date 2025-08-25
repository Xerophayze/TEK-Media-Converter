@echo off
setlocal

REM Configuration
set "VENV_DIR=venv"
set "SCRIPT_PATH=heic_to_jpg_gui.py"
title Image Converter

REM Shared progress UI files/flags
if not defined STATUS_FILE set "STATUS_FILE=%TEMP%\ic_setup_status.txt"
if not defined SETUP_FLAG set "SETUP_FLAG=%TEMP%\ic_setup_done.flag"
set "PROGRESS_STARTED="
set "PROG_CUR=0"
set "PROG_TOTAL=4"
set "IC_TOTAL_STEPS=%PROG_TOTAL%"
set "RERUN_FLAG=%TEMP%\ic_postinstall_rerun.flag"

REM Relaunch this script minimized once, then continue
if not defined BATCH_MINIMIZED (
    set "BATCH_MINIMIZED=1"
    start "" /min "%~f0" %*
    exit /b
)

:CHECK_PYTHON
echo Checking for Python...
where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        goto INSTALL_PYTHON
    )
)
echo Python found.
call :SETUP_ENV
goto :eof

:INSTALL_PYTHON
echo Python is not installed or not in the system's PATH.
echo Installing Python automatically...

REM Launch progress UI
set "PROG_CUR=0"
set "PROG_TOTAL=6"
set "IC_TOTAL_STEPS=%PROG_TOTAL%"
call :START_PROGRESS

echo Downloading Python installer...
call :STEP Downloading Python
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

echo Running Python installer silently. This may take a few minutes and require administrator permission...
call :STEP Installing Python
start "" /wait "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_tcltk=1 Include_test=0 SimpleInstall=1

if %errorlevel% neq 0 (
    echo Python installation failed. Please try installing it manually from python.org.
    if defined PROGRESS_STARTED (
        type nul > "%SETUP_FLAG%"
        timeout /t 1 /nobreak >nul
        del "%STATUS_FILE%" >nul 2>&1
    )
    pause
    exit /b 1
)

echo Python installation complete.
del "%TEMP%\python_installer.exe" >nul 2>&1
type nul > "%RERUN_FLAG%"
goto TRY_KNOWN_PATHS

:TRY_KNOWN_PATHS
REM Try to locate Python in common install locations and registry without relying on PATH
REM 1) Registry (3.12)
for /f "tokens=2,*" %%A in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.12\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "PY_BASE=%%B"
if defined PY_BASE if exist "%PY_BASE%python.exe" set "PYTHON_CMD=%PY_BASE%python.exe"

REM 2) Registry (3.11)
set "PY_BASE="
for /f "tokens=2,*" %%A in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "PY_BASE=%%B"
if defined PY_BASE if exist "%PY_BASE%python.exe" set "PYTHON_CMD=%PY_BASE%python.exe"

REM 3) Registry (HKCU, 3.12 then 3.11)
set "PY_BASE="
for /f "tokens=2,*" %%A in ('reg query "HKCU\SOFTWARE\Python\PythonCore\3.12\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "PY_BASE=%%B"
if defined PY_BASE if exist "%PY_BASE%python.exe" set "PYTHON_CMD=%PY_BASE%python.exe"
set "PY_BASE="
for /f "tokens=2,*" %%A in ('reg query "HKCU\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "PY_BASE=%%B"
if defined PY_BASE if exist "%PY_BASE%python.exe" set "PYTHON_CMD=%PY_BASE%python.exe"

REM 4) Registry (WOW6432Node, 32-bit)
set "PY_BASE="
for /f "tokens=2,*" %%A in ('reg query "HKLM\SOFTWARE\WOW6432Node\Python\PythonCore\3.11\InstallPath" /ve 2^>nul ^| find "REG_SZ"') do set "PY_BASE=%%B"
if defined PY_BASE if exist "%PY_BASE%python.exe" set "PYTHON_CMD=%PY_BASE%python.exe"

REM 5) Program Files common paths
if not defined PYTHON_CMD if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON_CMD=%ProgramFiles%\Python312\python.exe"
if not defined PYTHON_CMD if exist "%ProgramFiles%\Python311\python.exe" set "PYTHON_CMD=%ProgramFiles%\Python311\python.exe"
if not defined PYTHON_CMD if exist "%ProgramFiles(x86)%\Python311\python.exe" set "PYTHON_CMD=%ProgramFiles(x86)%\Python311\python.exe"

REM 6) Local AppData common paths
if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON_CMD=%LocalAppData%\Programs\Python\Python311\python.exe"

REM 7) Windows py launcher direct path
if not defined PYTHON_CMD if exist "%SystemRoot%\py.exe" set "PYTHON_CMD=%SystemRoot%\py.exe"

REM 8) Fallback to PATH search once more (in case PATH updated but current session didn't refresh)
if not defined PYTHON_CMD where py >nul 2>&1 && set "PYTHON_CMD=py"
if not defined PYTHON_CMD where python >nul 2>&1 && set "PYTHON_CMD=python"

if defined PYTHON_CMD (
    call :SETUP_ENV
    goto :eof
)

echo Python still not found after attempted installation.
echo Please close this window and re-run the script, or install Python manually from https://www.python.org/downloads/.
if defined PROGRESS_STARTED (
    type nul > "%SETUP_FLAG%"
    timeout /t 1 /nobreak >nul
    del "%STATUS_FILE%" >nul 2>&1
)
pause
exit /b 1

:SETUP_ENV
if not defined PROGRESS_STARTED call :INIT_PROGRESS 6
echo Verifying Tcl/Tk availability...
call :STEP Verifying Tcl/Tk
call :SET_TK_ENV
call :VERIFY_TCLTK
if exist "%VENV_DIR%\Scripts\activate.bat" goto VENV_DONE
echo Creating virtual environment...
call :STEP Creating virtual environment
"%PYTHON_CMD%" -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    if defined PROGRESS_STARTED (
        type nul > "%SETUP_FLAG%"
        timeout /t 1 /nobreak >nul
        del "%STATUS_FILE%" >nul 2>&1
    )
    pause
    exit /b 1
)
:VENV_DONE

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo Installing dependencies from requirements.txt...
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo Virtual environment Python not found at "%VENV_PY%".
    echo Venv creation may have failed. Please re-run this script.
    if defined PROGRESS_STARTED (
        type nul > "%SETUP_FLAG%"
        timeout /t 1 /nobreak >nul
        del "%STATUS_FILE%" >nul 2>&1
    )
    pause
    exit /b 1
)

set "REQ_FILE=requirements.txt"
if not exist "%REQ_FILE%" (
    echo %REQ_FILE% not found. Creating a basic one...
    > "%REQ_FILE%" echo Pillow
    >> "%REQ_FILE%" echo pillow-heif
    >> "%REQ_FILE%" echo tkinterdnd2
)

call :STEP Upgrading pip
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
call :STEP Installing dependencies
"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if %errorlevel% neq 0 (
    echo Dependency install failed. Bootstrapping pip with ensurepip and retrying once...
    call :STEP Bootstrapping pip
    "%VENV_PY%" -m ensurepip --upgrade
    "%VENV_PY%" -m pip install --upgrade pip setuptools wheel
    REM Avoid parentheses in echoed text to prevent batch parse issues
    call :STEP Installing dependencies - retry
    "%VENV_PY%" -m pip install -r "%REQ_FILE%"
    if %errorlevel% neq 0 (
        echo Failed to install dependencies after retry.
        if defined PROGRESS_STARTED (
            type nul > "%SETUP_FLAG%"
            timeout /t 1 /nobreak >nul
            del "%STATUS_FILE%" >nul 2>&1
        )
        pause
        exit /b 1
    )
)

REM Close progress UI if it was started
if defined PROGRESS_STARTED (
    type nul > "%SETUP_FLAG%"
    timeout /t 1 /nobreak >nul
    del "%STATUS_FILE%" >nul 2>&1
    del "%SETUP_FLAG%" >nul 2>&1
)

REM Create Desktop shortcut (once) pointing to this launcher with custom icon
for /f "usebackq tokens=*" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"
set "SCRIPT_DIR=%~dp0"
set "SHORTCUT=%DESKTOP%\Image Converter.lnk"
set "TARGET=%SCRIPT_DIR%run_converter.bat"
set "WORKDIR=%SCRIPT_DIR%"
set "ICON=%SCRIPT_DIR%resources\tekutah_logo_icon_Square.ico"

if not exist "%SHORTCUT%" (
    echo Creating desktop shortcut...
) else (
    echo Updating desktop shortcut icon...
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($env:SHORTCUT); $s.TargetPath = $env:TARGET; $s.WorkingDirectory = $env:WORKDIR; if (Test-Path $env:ICON) { $s.IconLocation = $env:ICON }; $s.WindowStyle = 7; $s.Save()"

REM Ensure Tcl/Tk env for first run (safe invocation)
set "IC_TMP=%TEMP%\ic_pybase_final.txt"
"%VENV_PY%" -c "import sys;print(sys.base_prefix)" > "%IC_TMP%" 2>nul
set /p PY_BASE_FINAL=<"%IC_TMP%"
del "%IC_TMP%" >nul 2>&1
if exist "%PY_BASE_FINAL%\tcl\tcl8.6\init.tcl" set "TCL_LIBRARY=%PY_BASE_FINAL%\tcl\tcl8.6"
if exist "%PY_BASE_FINAL%\tcl\tk8.6\tk.tcl" set "TK_LIBRARY=%PY_BASE_FINAL%\tcl\tk8.6"
if exist "%PY_BASE_FINAL%\DLLs" set "PATH=%PY_BASE_FINAL%\DLLs;%PY_BASE_FINAL%;%PATH%"

echo Starting Image Converter...
if exist "%RERUN_FLAG%" (
    echo Relaunching once to finalize environment...
    del "%RERUN_FLAG%" >nul 2>&1
    if defined PROGRESS_STARTED (
        type nul > "%SETUP_FLAG%"
        timeout /t 1 /nobreak >nul
        del "%STATUS_FILE%" >nul 2>&1
    )
    start "" /min "%~f0" %*
    exit /b
)
"%VENV_PY%" "%SCRIPT_PATH%"

REM Close this console window after the GUI exits
exit

endlocal

goto :eof

:START_PROGRESS
set "PROGRESS_STARTED=1"
del "%SETUP_FLAG%" >nul 2>&1
del "%STATUS_FILE%" >nul 2>&1
set "PS_FILE=%~dp0resources\setup_progress.ps1"
start "" powershell -NoProfile -WindowStyle Hidden -STA -ExecutionPolicy Bypass -File "%PS_FILE%"
exit /b 0

:INIT_PROGRESS
set "PROG_CUR=0"
set "PROG_TOTAL=%~1"
if "%PROG_TOTAL%"=="" set "PROG_TOTAL=4"
set "IC_TOTAL_STEPS=%PROG_TOTAL%"
call :START_PROGRESS
exit /b 0

:STEP
set /a PROG_CUR+=1
set "STEP_MSG=%*"
> "%STATUS_FILE%" echo %PROG_CUR% ^| %STEP_MSG%
exit /b 0

:SET_TK_ENV
 set "PY_BASE_READY="
 set "IC_TMP=%TEMP%\ic_pybase_ready.txt"
 if /i "%PYTHON_CMD%"=="py" (
  py -c "import sys;print(sys.base_prefix)" > "%IC_TMP%" 2>nul
 ) else if /i "%PYTHON_CMD%"=="python" (
  python -c "import sys;print(sys.base_prefix)" > "%IC_TMP%" 2>nul
 ) else (
  "%PYTHON_CMD%" -c "import sys;print(sys.base_prefix)" > "%IC_TMP%" 2>nul
 )
 set /p PY_BASE_READY=<"%IC_TMP%"
 del "%IC_TMP%" >nul 2>&1
 if defined PY_BASE_READY (
  if exist "%PY_BASE_READY%\tcl\tcl8.6\init.tcl" set "TCL_LIBRARY=%PY_BASE_READY%\tcl\tcl8.6"
  if exist "%PY_BASE_READY%\tcl\tk8.6\tk.tcl" set "TK_LIBRARY=%PY_BASE_READY%\tcl\tk8.6"
  if exist "%PY_BASE_READY%\DLLs" set "PATH=%PY_BASE_READY%\DLLs;%PY_BASE_READY%;%PATH%"
 )
 exit /b 0

:VERIFY_TCLTK
 set "TK_OK="
 for /L %%I in (1,1,10) do (
  if /i "%PYTHON_CMD%"=="py" (
    py -c "import tkinter as tk; tk.Tk().destroy()" >nul 2>&1 && (set "TK_OK=1" & goto :VTK_OK)
  ) else if /i "%PYTHON_CMD%"=="python" (
    python -c "import tkinter as tk; tk.Tk().destroy()" >nul 2>&1 && (set "TK_OK=1" & goto :VTK_OK)
  ) else (
    "%PYTHON_CMD%" -c "import tkinter as tk; tk.Tk().destroy()" >nul 2>&1 && (set "TK_OK=1" & goto :VTK_OK)
  )
  echo Waiting for Tcl/Tk to become available... ^(attempt %%I/10^)
  timeout /t 2 /nobreak >nul
 )
:VTK_OK
 exit /b 0
