"""
updater.py — checks GitHub releases for a newer version and handles
the download / replace / relaunch flow.
"""

import os
import sys
import ssl
import threading
import zipfile
import urllib.request
import json
import tempfile
import subprocess

from version import VERSION

GITHUB_API   = "https://api.github.com/repos/Leoncrispybacon/Full-Auto-Forza-Edition/releases/latest"
TIMEOUT      = 8   # seconds for API request


def _make_ssl_context():
    """SSL context backed by certifi's CA bundle.

    A frozen app's Python `ssl` falls back to the OS cert store, which on some
    Windows installs (notably handhelds whose root-cert store was never
    populated) is missing the issuer cert — HTTPS to GitHub then dies with
    'CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate'. certifi
    ships the Mozilla CA bundle WITH the app, so verification no longer depends
    on the device. Falls back to the default context if certifi is unavailable."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None


# Built once at import; passed to every urlopen so both the version check and
# the download use the bundled CA bundle.
_SSL_CTX = _make_ssl_context()

# Reason the last fetch_latest() failed (None on success). Lets the UI log WHY
# an update check came back empty instead of failing silently — important for
# diagnosing devices where the check never surfaces a dialog (network/SSL/clock
# skew/rate-limit).
_last_error = None


def _parse_version(tag: str):
    """'v1.0.2' → (1, 0, 2)"""
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def fetch_latest():
    """
    Returns (latest_tag, download_url) or (None, None) on any error.
    download_url points to the first .zip asset in the release.
    """
    global _last_error
    _last_error = None
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "FAFE-updater"}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT,
                                    context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode())
        tag   = data.get("tag_name", "")
        assets = data.get("assets", [])
        url   = next(
            (a["browser_download_url"] for a in assets
             if a["browser_download_url"].endswith(".zip")),
            None
        )
        if not tag:
            _last_error = "GitHub returned no tag_name (rate-limited?)"
        return tag, url
    except Exception as e:
        _last_error = f"{type(e).__name__}: {e}"
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
            with urllib.request.urlopen(zip_url, timeout=60,
                                        context=_SSL_CTX) as resp:
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

            # ── Write updater.bat — replace FAFE.exe, _internal/, and preset
            # templates while preserving the user's templates/.../custom/
            # folders and their config.json.
            #
            # Copy is retried while FAFE.exe is still locked; if it ultimately
            # fails, skip the destructive /PURGE on _internal and relaunch the
            # existing exe so the user isn't left with a broken install.
            # Template copy failures are non-fatal — the app is already
            # updated, the user can recapture if a preset is bad.
            src_exe      = os.path.join(src_dir, "FAFE.exe")
            src_internal = os.path.join(src_dir, "_internal")

            # Preset template folders to refresh (custom/ folders are
            # implicitly preserved — never written to).
            tpl_pairs: list[tuple[str, str]] = []
            for category in ("race", "mastery_full"):
                for preset in ("1080p", "1440p", "2160p"):
                    tpl_pairs.append((
                        os.path.join(src_dir, "templates", category, preset),
                        os.path.join(exe_dir, "templates", category, preset),
                    ))
            tpl_pairs.append((
                os.path.join(src_dir, "templates", "examples"),
                os.path.join(exe_dir, "templates", "examples"),
            ))
            tpl_lines = "".join(
                f'robocopy "{src}" "{dst}" /E /IS /IT /IM /PURGE >nul\n'
                for src, dst in tpl_pairs
            )

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
                + tpl_lines +
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


def check_async(on_update_available, on_status=None):
    """
    Checks for updates in a background thread.
    Calls on_update_available(latest_tag, download_url) if a newer version is
    found. `on_status(msg)` (optional) receives a human-readable diagnostic at
    each outcome so the check is never silent — critical for figuring out why a
    device (e.g. a handheld) never shows the update dialog.
    """
    def _say(msg):
        if on_status:
            try:
                on_status(msg)
            except Exception:
                pass

    def _check():
        _say(f"checking for updates (installed v{VERSION})…")
        tag, url = fetch_latest()
        if not tag:
            _say(f"update check failed: {_last_error or 'unknown error'}")
            return
        if not is_newer(tag):
            _say(f"up to date (latest {tag})")
            return
        if not url:
            _say(f"update {tag} found, but it has no .zip asset to download")
            return
        _say(f"update available: {tag}")
        on_update_available(tag, url)

    threading.Thread(target=_check, daemon=True).start()
