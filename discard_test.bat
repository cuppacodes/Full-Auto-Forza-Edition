@echo off
:: ============================================================
::  discard_test.bat — abandon the current test branch entirely.
::
::  Use when test changes didn't work out and you want main
::  untouched, with all evidence of the test branch removed.
:: ============================================================

cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Detect current branch
for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD') do set "BR=%%i"

if "%BR%"=="main" (
    echo You're already on main.  Switch to the test branch first
    echo with: git checkout test/your-branch-name
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   DISCARD test branch:  %BR%
echo  ============================================================
echo.
echo  This will PERMANENTLY THROW AWAY all changes on %BR% and:
echo    1. Switch to main
echo    2. Delete %BR% locally
echo    3. Delete %BR% on GitHub
echo.
echo  Main branch is not touched.
echo.
set /p OK="Type 'yes' to proceed: "
if /i not "%OK%"=="yes" (
    echo Aborted.  Nothing changed.
    pause
    exit /b 0
)

echo.
echo [1/3] Switching to main...
git checkout main || goto :fail

echo [2/3] Deleting %BR% locally...
git branch -D "%BR%" || goto :fail

echo [3/3] Deleting %BR% on GitHub...
git push origin --delete "%BR%" || (
    echo   Warning: remote delete failed ^(branch may already be gone^).
)

echo.
echo  ============================================================
echo   DONE  -  %BR% discarded.  Main is unchanged.
echo  ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo  ============================================================
echo   FAILED  -  see error above.
echo  ============================================================
echo.
pause
exit /b 1
