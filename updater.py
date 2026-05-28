"""
updater.py — checks GitHub releases for a newer version and handles
the download / replace / relaunch flow.
"""

import os
import sys
import threading
import zipfile
import urllib.request
import json
import tempfile
import subprocess

from version import VERSION

GITHUB_API   = "https://api.github.com/repos/Leoncrispybacon/Full-Auto-Forza-Edition/releases/latest"
TIMEOUT      = 8   # seconds for API request


def _parse_version(tag: str):
    """'v1.0.2' → (1, 0, 2)"""
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def fetch_latest():
    """
    Returns (latest_tag, download_url) or (None, None) on any error.
    download_url points to the first .zip asset in the release.
    """
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "FAFE-updater"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        tag   = data.get("tag_name", "")
        assets = data.get("assets", [])
        url   = next(
            (a["browser_download_url"] for a in assets
             if a["browser_download_url"].endswith(".zip")),
            None
        )
        return tag, url
    except Exception:
        return None, None


def is_newer(latest_tag: str) -> bool:
    try:
        return _parse_version(latest_tag) > _parse_version(VERSION)
    except Exception:
        return False


def download_and_install(zip_url: str, progress_cb=None, done_cb=None):
    """
    Downloads zip_url, extracts FAFE.exe, writes an updater.bat that
    replaces the running exe and relaunches it, then exits the app.

    progress_cb(pct: int)  — called with 0–100 during download
    done_cb(success: bool) — called when complete
    """
    def _run():
        try:
            exe_path = sys.executable if getattr(sys, "frozen", False) \
                       else os.path.abspath(sys.argv[0])
            exe_dir  = os.path.dirname(exe_path)
            exe_name = os.path.basename(exe_path)

            # ── Download zip ──────────────────────────────────
            tmp_zip = os.path.join(tempfile.gettempdir(), "FAFE_update.zip")
            with urllib.request.urlopen(zip_url, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 65536
                with open(tmp_zip, "wb") as f:
                    while True:
                        buf = resp.read(chunk)
                        if not buf:
                            break
                        f.write(buf)
                        downloaded += len(buf)
                        if total and progress_cb:
                            progress_cb(int(downloaded * 100 / total))

            if progress_cb:
                progress_cb(100)

            # ── Extract full zip to temp folder ──────────────
            import shutil
            tmp_extract = os.path.join(tempfile.gettempdir(), "FAFE_update_extract")
            if os.path.exists(tmp_extract):
                shutil.rmtree(tmp_extract)
            os.makedirs(tmp_extract)

            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(tmp_extract)

            os.remove(tmp_zip)

            # Find the root folder inside the zip
            entries = os.listdir(tmp_extract)
            if len(entries) == 1 and os.path.isdir(os.path.join(tmp_extract, entries[0])):
                src_dir = os.path.join(tmp_extract, entries[0])
            else:
                src_dir = tmp_extract

            # ── Write updater.bat — only replace FAFE.exe and _internal/ ──
            # Copy is retried while FAFE.exe is still locked; if it ultimately
            # fails, skip the destructive /PURGE on _internal and relaunch the
            # existing exe so the user isn't left with a broken install.
            src_exe      = os.path.join(src_dir, "FAFE.exe")
            src_internal = os.path.join(src_dir, "_internal")
            bat_path = os.path.join(tempfile.gettempdir(), "fafe_update.bat")
            bat = (
                "@echo off\n"
                "setlocal enabledelayedexpansion\n"
                "timeout /t 2 /nobreak >nul\n"
                "set /a TRIES=10\n"
                ":try_copy\n"
                f'copy /y "{src_exe}" "{exe_path}" >nul 2>&1\n'
                "if not errorlevel 1 goto copy_ok\n"
                "set /a TRIES-=1\n"
                "if !TRIES! LEQ 0 goto fail\n"
                "timeout /t 1 /nobreak >nul\n"
                "goto try_copy\n"
                ":copy_ok\n"
                f'robocopy "{src_internal}" "{exe_dir}\\_internal" /E /IS /IT /IM /PURGE >nul\n'
                "if errorlevel 8 goto fail\n"
                f'start "" "{exe_path}"\n'
                f'rmdir /s /q "{tmp_extract}" >nul 2>&1\n'
                'del "%~f0"\n'
                "exit /b 0\n"
                ":fail\n"
                f'start "" "{exe_path}"\n'
                f'rmdir /s /q "{tmp_extract}" >nul 2>&1\n'
                'del "%~f0"\n'
                "exit /b 1\n"
            )
            with open(bat_path, "w") as f:
                f.write(bat)

            # ── Launch bat and exit ───────────────────────────
            subprocess.Popen(
                ["cmd", "/c", bat_path],
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if done_cb:
                done_cb(True)

            # Give done_cb a moment to update UI before we exit
            import time
            time.sleep(0.5)
            os._exit(0)

        except Exception as e:
            if done_cb:
                done_cb(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def check_async(on_update_available):
    """
    Checks for updates in a background thread.
    Calls on_update_available(latest_tag, download_url) if a newer
    version is found. Silent on error or if already up to date.
    """
    def _check():
        tag, url = fetch_latest()
        if tag and url and is_newer(tag):
            on_update_available(tag, url)

    threading.Thread(target=_check, daemon=True).start()
