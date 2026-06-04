"""
updater.py — checks GitHub releases for a newer version.

IMPORTANT: FAFE no longer downloads or installs anything itself.
  - Nexus Mods prohibits bundled executables from downloading/sending files
    over the internet (auto-update is explicitly NOT considered "crucial").
  - A self-updater that downloads a zip, runs a .bat and overwrites its own exe
    is also the single biggest antivirus false-positive trigger (Defender was
    quarantining FAFE on users' machines because of it).

So this module only CHECKS whether a newer release exists. If one does, the UI
shows a notice and the user opens the releases page in their browser to download
manually (opening a URL hands off to the browser — the exe itself makes no
download). The version check can be disabled entirely via the `update_check`
config flag for a fully offline / Nexus-safe build.
"""

import ssl
import threading
import urllib.request
import json

from version import VERSION

GITHUB_API    = "https://api.github.com/repos/Leoncrispybacon/Full-Auto-Forza-Edition/releases/latest"
RELEASES_PAGE = "https://github.com/Leoncrispybacon/Full-Auto-Forza-Edition/releases/latest"
TIMEOUT       = 8   # seconds for the version-check request


def _make_ssl_context():
    """SSL context backed by certifi's CA bundle so the version check works on
    machines whose OS root-cert store is incomplete (e.g. some handhelds), which
    otherwise fail with CERTIFICATE_VERIFY_FAILED."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None


_SSL_CTX = _make_ssl_context()

# Reason the last fetch_latest() failed (None on success), so the UI can log WHY
# a check came back empty instead of failing silently.
_last_error = None


def _parse_version(tag: str):
    """'v1.0.2' → (1, 0, 2)"""
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def fetch_latest():
    """Return (latest_tag, releases_page_url) or (None, None) on any error.
    Only reads the tag name — it does NOT download any asset."""
    global _last_error
    _last_error = None
    try:
        req = urllib.request.Request(
            GITHUB_API, headers={"User-Agent": "FAFE-updater"})
        with urllib.request.urlopen(req, timeout=TIMEOUT,
                                    context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode())
        tag = data.get("tag_name", "")
        if not tag:
            _last_error = "GitHub returned no tag_name (rate-limited?)"
        return tag, RELEASES_PAGE
    except Exception as e:
        _last_error = f"{type(e).__name__}: {e}"
        return None, None


def is_newer(latest_tag: str) -> bool:
    try:
        return _parse_version(latest_tag) > _parse_version(VERSION)
    except Exception:
        return False


def check_async(on_update_available, on_status=None):
    """Check for a newer release in a background thread (read-only — no download).
    Calls on_update_available(latest_tag, releases_page_url) if a newer version
    exists. on_status(msg) reports the outcome for diagnostics."""
    def _say(msg):
        if on_status:
            try:
                on_status(msg)
            except Exception:
                pass

    def _check():
        _say(f"checking for updates (installed v{VERSION})…")
        tag, page = fetch_latest()
        if not tag:
            _say(f"update check failed: {_last_error or 'unknown error'}")
            return
        if not is_newer(tag):
            _say(f"up to date (latest {tag})")
            return
        _say(f"update available: {tag}")
        on_update_available(tag, page)

    threading.Thread(target=_check, daemon=True).start()
