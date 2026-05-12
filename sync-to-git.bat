@echo off
setlocal EnableDelayedExpansion

REM ============================================================
REM  sync-to-git.bat  -  TEK Media Converter project
REM  Repository: https://github.com/Xerophayze/TEK-Media-Converter.git
REM  Supports: push (commit + push), pull, status, and setup check.
REM  Run from the ImageConverter project root folder.
REM ============================================================

set "REPO_DIR=%~dp0"
if "%REPO_DIR:~-1%"=="\" set "REPO_DIR=%REPO_DIR:~0,-1%"
set "REMOTE=origin"
set "BRANCH=main"
set "REPO_URL=https://github.com/Xerophayze/TEK-Media-Converter.git"

call :ensure_git_available
if errorlevel 1 goto :done

call :ensure_repo
if errorlevel 1 goto :done

echo.
echo  ==================================================
echo   TEK Media Converter - GitHub Sync
echo   Repo: %REPO_URL%
echo   Branch: %BRANCH%
echo  ==================================================
echo.
echo   1. Push  (commit local changes and push to GitHub)
echo   2. Pull  (pull latest changes from GitHub)
echo   3. Status (show git status and recent log)
echo   4. Setup Check (verify repo, remote, and ignored files)
echo   5. Exit
echo.
set /p "CHOICE=Select an option [1-5]: "

if "!CHOICE!"=="1" goto :do_push
if "!CHOICE!"=="2" goto :do_pull
if "!CHOICE!"=="3" goto :do_status
if "!CHOICE!"=="4" goto :do_setup_check
if "!CHOICE!"=="5" goto :done
echo Invalid choice. Exiting.
goto :done

REM ============================================================
:do_push
REM ============================================================
call :ensure_clean_remote_config
if errorlevel 1 goto :done

echo.
echo --- Checking for changes ---
git -C "%REPO_DIR%" status --short
echo.

git -C "%REPO_DIR%" diff --quiet && git -C "%REPO_DIR%" diff --cached --quiet
if %errorlevel%==0 (
    echo Nothing to commit - working tree is clean.
    echo.
    echo Pushing any unpushed commits...
    git -C "%REPO_DIR%" push -u %REMOTE% %BRANCH%
    if errorlevel 1 (
        echo ERROR: git push failed.
        echo If GitHub has newer commits, run option 2 Pull first, resolve any conflicts, then push again.
        pause
        exit /b 1
    )
    echo Push complete.
    goto :done
)

echo --- Safety check: scanning for generated and sensitive files ---
call :check_blocked_files
if errorlevel 1 goto :done

echo --- Staging all changes ---
git -C "%REPO_DIR%" add -A
if errorlevel 1 (
    echo ERROR: git add failed.
    pause
    exit /b 1
)

echo.
set /p "COMMIT_MSG=Enter commit message (or press Enter for default): "
if "!COMMIT_MSG!"=="" set "COMMIT_MSG=chore: sync image converter changes"

echo --- Committing ---
git -C "%REPO_DIR%" commit -m "!COMMIT_MSG!"
if errorlevel 1 (
    echo ERROR: git commit failed.
    pause
    exit /b 1
)

echo.
echo --- Pushing to GitHub ---
git -C "%REPO_DIR%" push -u %REMOTE% %BRANCH%
if errorlevel 1 (
    echo ERROR: git push failed. You may need to pull first if the remote has new commits.
    pause
    exit /b 1
)

echo.
echo Push complete!
goto :done

REM ============================================================
:do_pull
REM ============================================================
call :ensure_clean_remote_config
if errorlevel 1 goto :done

echo.
echo --- Fetching from GitHub ---
git -C "%REPO_DIR%" fetch %REMOTE%
if errorlevel 1 (
    echo ERROR: git fetch failed. Check your network or credentials.
    pause
    exit /b 1
)

echo.
echo --- Pulling %REMOTE%/%BRANCH% into %BRANCH% ---
git -C "%REPO_DIR%" pull --rebase %REMOTE% %BRANCH%
if errorlevel 1 (
    echo ERROR: git pull failed. You may have local changes or conflicts to resolve.
    echo If this folder was not cloned from GitHub, commit local changes first, then pull again.
    pause
    exit /b 1
)

echo.
echo Pull complete!
goto :done

REM ============================================================
:do_status
REM ============================================================
call :ensure_clean_remote_config
if errorlevel 1 goto :done

echo.
echo --- Git Status ---
git -C "%REPO_DIR%" status
echo.
echo --- Remote ---
git -C "%REPO_DIR%" remote -v
echo.
echo --- Recent Commits ---
git -C "%REPO_DIR%" log --oneline -10
echo.
pause
goto :eof

REM ============================================================
:do_setup_check
REM ============================================================
call :ensure_clean_remote_config
if errorlevel 1 goto :done

echo.
echo --- Repository Check ---
git -C "%REPO_DIR%" status --short
echo.
git -C "%REPO_DIR%" remote -v
echo.
echo --- Ignore Check ---
git -C "%REPO_DIR%" check-ignore -v venv resources/ffmpeg 2>nul
echo.
call :check_blocked_files
echo.
pause
goto :eof

REM ============================================================
:ensure_git_available
REM ============================================================
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not available on PATH.
    echo Install Git for Windows, then run this script again.
    exit /b 1
)
exit /b 0

REM ============================================================
:ensure_repo
REM ============================================================
set "NEW_REPO="
if not exist "%REPO_DIR%\.git" (
    echo.
    echo Git repository not found. Initializing this folder...
    git -C "%REPO_DIR%" init
    if errorlevel 1 (
        echo ERROR: git init failed.
        exit /b 1
    )
    set "NEW_REPO=1"
)

call :ensure_clean_remote_config
if errorlevel 1 exit /b 1

git -C "%REPO_DIR%" rev-parse --verify HEAD >nul 2>&1
if errorlevel 1 (
    echo.
    echo No local commits found. Attaching this folder to %REMOTE%/%BRANCH% as the baseline...
    git -C "%REPO_DIR%" fetch %REMOTE% %BRANCH%
    if errorlevel 1 (
        echo ERROR: Could not fetch %REMOTE%/%BRANCH%.
        exit /b 1
    )
    git -C "%REPO_DIR%" checkout -B %BRANCH% >nul 2>&1
    git -C "%REPO_DIR%" reset --mixed %REMOTE%/%BRANCH%
    if errorlevel 1 (
        echo ERROR: Could not attach local branch to %REMOTE%/%BRANCH%.
        exit /b 1
    )
    if not exist "%REPO_DIR%\TEKImageConverter_installer.exe" (
        git -C "%REPO_DIR%" checkout -- TEKImageConverter_installer.exe >nul 2>&1
    )
    exit /b 0
)

git -C "%REPO_DIR%" checkout -B %BRANCH% >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not switch to branch %BRANCH%.
    exit /b 1
)
exit /b 0

REM ============================================================
:ensure_clean_remote_config
REM ============================================================
git -C "%REPO_DIR%" remote get-url %REMOTE% >nul 2>&1
if errorlevel 1 (
    git -C "%REPO_DIR%" remote add %REMOTE% %REPO_URL%
) else (
    git -C "%REPO_DIR%" remote set-url %REMOTE% %REPO_URL%
)
if errorlevel 1 (
    echo ERROR: Could not configure remote %REMOTE%.
    exit /b 1
)
exit /b 0

REM ============================================================
:check_blocked_files
REM Abort if generated folders or sensitive files would be staged.
REM ============================================================
set "FOUND_BLOCKED="
for %%F in (
    "%REPO_DIR%\venv"
    "%REPO_DIR%\resources\ffmpeg"
    "%REPO_DIR%\.env"
    "%REPO_DIR%\.env.local"
    "%REPO_DIR%\*.pem"
    "%REPO_DIR%\*.key"
    "%REPO_DIR%\*.pfx"
    "%REPO_DIR%\*.p12"
) do (
    if exist %%F (
        git -C "%REPO_DIR%" check-ignore -q %%F 2>nul
        if errorlevel 1 (
            echo.
            echo  *** FILE OR FOLDER SHOULD BE IGNORED BEFORE PUSHING ***
            echo  %%F
            echo.
            set "FOUND_BLOCKED=1"
        )
    )
)
git -C "%REPO_DIR%" ls-files --error-unmatch TEKImageConverter_installer.exe >nul 2>&1
if not errorlevel 1 (
    if not exist "%REPO_DIR%\TEKImageConverter_installer.exe" (
        echo.
        echo  *** TRACKED INSTALLER IS MISSING ***
        echo  %REPO_DIR%\TEKImageConverter_installer.exe
        echo  Restore it before pushing unless you intend to remove it from GitHub.
        echo.
        set "FOUND_BLOCKED=1"
    )
)
if defined FOUND_BLOCKED (
    echo Aborting push. Update .gitignore before syncing.
    pause
    exit /b 1
)
echo  No exposed generated or sensitive files detected.
exit /b 0

REM ============================================================
:done
REM ============================================================
echo.
pause
