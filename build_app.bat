@echo off
:: Change to the folder containing this bat file
cd /d "%~dp0"

title Forza Auto App - Build

:: Clean up old build artifacts to avoid permission errors
taskkill /f /im FAFE.exe >nul 2>&1
timeout /t 1 /nobreak >nul
if exist dist rmdir /s /q dist >nul 2>&1
if exist build rmdir /s /q build >nul 2>&1
if exist FAFE.spec del /f /q FAFE.spec >nul 2>&1
if exist FAFE_dist rmdir /s /q FAFE_dist >nul 2>&1

echo.
echo  =====================================================
echo   Full Auto Forza Edition - Building FAFE.exe
echo  =====================================================
echo.
pause

:: -- Step 1: Install dependencies ----------------------------
echo.
echo  [1/2]  Installing dependencies...
echo  -----------------------------------------------------
pip install --upgrade pyinstaller customtkinter Pillow ^
    pydirectinput opencv-python ^
    mss numpy keyboard requests certifi ^
    rapidocr-onnxruntime
if errorlevel 1 (
    echo.
    echo  ERROR: pip failed. Check Python installation.
    echo.
    pause
    exit /b 1
)

:: -- Step 2: Build FAFE.exe ----------------------------------
echo.
echo  [2/2]  Building FAFE.exe...
echo  -----------------------------------------------------
python -m PyInstaller --onedir --windowed --name FAFE ^
    --icon "%CD%\FAFE_icon.ico" ^
    --add-data "%CD%\FAFE_icon.ico;." ^
    --add-data "%CD%\assets;assets" ^
    --add-data "%CD%\app_lang.py;." ^
    --add-data "%CD%\config.py;." ^
    --add-data "%CD%\capture.py;." ^
    --add-data "%CD%\detector.py;." ^
    --add-data "%CD%\theme.py;." ^
    --add-data "%CD%\race.py;." ^
    --add-data "%CD%\mastery.py;." ^
    --add-data "%CD%\main_window.py;." ^
    --add-data "%CD%\setup_panel.py;." ^
    --add-data "%CD%\log_widget.py;." ^
    --add-data "%CD%\version.py;." ^
    --add-data "%CD%\updater.py;." ^
    --add-data "%CD%\delete_cars.py;." ^
    --add-data "%CD%\report.py;." ^
    --add-data "%CD%\overlay.py;." ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import detector ^
    --hidden-import rapidocr_onnxruntime ^
    --hidden-import asyncio ^
    --hidden-import asyncio.base_events ^
    --hidden-import asyncio.events ^
    --hidden-import asyncio.futures ^
    --hidden-import asyncio.tasks ^
    --hidden-import urllib.request ^
    --hidden-import zipfile ^
    --hidden-import certifi ^
    --collect-all customtkinter ^
    --collect-all rapidocr_onnxruntime ^
    --collect-all certifi ^
    forza_app.py
if errorlevel 1 (
    echo.
    echo  ERROR: Build failed. See output above.
    echo.
    pause
    exit /b 1
)

if exist FAFE_dist rmdir /s /q FAFE_dist >nul 2>&1
xcopy /e /i /q dist\FAFE FAFE_dist >nul

:: -- Step 3: Generate default config.json -------------------
echo  [+]    Writing default config.json...
(
  echo {
  echo   "lang": "zh-tw",
  echo   "theme": "system",
  echo   "toggle_key": "f9",
  echo   "capture_key": "caps lock",
  echo   "monitor_index": 1,
  echo   "race_resolution": "1080p",
  echo   "mastery_resolution": "1080p",
  echo   "race_threshold": 0.6,
  echo   "thresh_start_menu": 0.5,
  echo   "thresh_racing": 0.5,
  echo   "thresh_restart_menu": 0.5,
  echo   "thresh_confirm": 0.5,
  echo   "thresh_mastery_ride_car": 0.6,
  echo   "thresh_mastery_esc_hint": 0.6,
  echo   "thresh_mastery_upgrade_item": 0.5,
  echo   "thresh_mastery_mastery_item": 0.6,
  echo   "thresh_mastery_anchor": 0.6,
  echo   "thresh_mastery_my_cars": 0.6,
  echo   "thresh_mastery_sort_recent": 0.6,
  echo   "race_check_interval": 0.5,
  echo   "race_post_key_wait": 0.75,
  echo   "mastery_threshold": 0.85,
  echo   "mastery_check_interval": 0.5,
  echo   "mastery_start_loop": 1,
  echo   "mastery_post_click_wait": 0.8,
  echo   "mastery_post_key_wait": 1.2,
  echo   "mastery_node_click_wait": 0.8,
  echo   "buy_post_key_wait": 0.5,
  echo   "delete_post_key_wait": 0.5
  echo }
) > FAFE_dist\config.json

echo.
echo  =====================================================
echo   BUILD COMPLETE
echo  =====================================================
echo.
echo  FAFE.exe is ready in FAFE_dist\.
echo.
echo  Templates will be saved to a 'templates' subfolder
echo  next to the exe automatically.
echo.
echo  You can delete 'dist', 'build', and FAFE.spec.
echo.
pause
