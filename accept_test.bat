@echo off
:: ============================================================
::  accept_test.bat — merge the current test branch into main,
::  push, and delete the test branch.
::
::  Run this from a test branch when you're happy with the
::  changes and want to make them official.
:: ============================================================

cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Detect current branch
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD') do set "BR=%%i"

if "%BR%"=="main" (
    echo You're already on main.  Switch to a test branch first
    echo with: git checkout test/your-branch-name
    echo.
    pause
    exit /b 1
)

:: Refuse if working tree is dirty — easier than dealing with merge conflicts
git diff-index --quiet HEAD >nul 2>&1
if errorlevel 1 (
    echo You have uncommitted changes on %BR%.
    echo Commit them first, then re-run this script.
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   ACCEPT test branch:  %BR%
echo  ============================================================
echo.
echo  This will:
echo    1. Switch to main
echo    2. Merge %BR% into main
echo    3. Push main to GitHub
echo    4. Delete %BR% (locally and on GitHub)
echo.
set /p OK="Type 'yes' to proceed: "
if /i not "%OK%"=="yes" (
    echo Aborted.  Nothing changed.
    pause
    exit /b 0
)

echo.
echo [1/4] Switching to main...
git checkout main || goto :fail

echo [2/4] Merging %BR%...
git merge "%BR%" || goto :fail

echo [3/4] Pushing main to GitHub...
git push origin main || goto :fail

echo [4/4] Deleting %BR%...
git branch -d "%BR%" || goto :fail
git push origin --delete "%BR%" || (
    echo   Warning: remote delete failed ^(branch may already be gone^).
)

echo.
echo  ============================================================
echo   SUCCESS  -  %BR% merged into main and deleted.
echo  ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo  ============================================================
echo   FAILED  -  see error above.  Nothing further was done.
echo  ============================================================
echo.
pause
exit /b 1
