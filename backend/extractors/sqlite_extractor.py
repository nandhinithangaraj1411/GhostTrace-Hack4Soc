# backend/extractors/sqlite_extractor.py

import os
import sqlite3
import shutil
import tempfile
from pathlib import Path

LOCAL = Path(os.environ.get("LOCALAPPDATA", ""))
ROAMING = Path(os.environ.get("APPDATA", ""))

BROWSERS = {
    "Edge": {
        "type": "chromium",
        "path": LOCAL / "Microsoft" / "Edge" / "User Data"
    },
    "Chrome": {
        "type": "chromium",
        "path": LOCAL / "Google" / "Chrome" / "User Data"
    },
    "Brave": {
        "type": "chromium",
        "path": LOCAL / "BraveSoftware" / "Brave-Browser" / "User Data"
    },
    "Firefox": {
        "type": "firefox",
        "path": ROAMING / "Mozilla" / "Firefox" / "Profiles"
    }
}


def get_chromium_profiles(user_data_path):
    profiles = []

    if not user_data_path.exists():
        return profiles

    for folder in user_data_path.iterdir():
        if folder.is_dir() and (
            folder.name == "Default"
            or folder.name.startswith("Profile")
        ):
            cookie_db = folder / "Network" / "Cookies"

            if cookie_db.exists():
                profiles.append({
                    "profile_name": folder.name,
                    "cookie_db": cookie_db
                })

    return profiles


def get_firefox_profiles(profiles_path):
    profiles = []

    if not profiles_path.exists():
        return profiles

    for folder in profiles_path.iterdir():
        if folder.is_dir():
            cookie_db = folder / "cookies.sqlite"

            if cookie_db.exists():
                profiles.append({
                    "profile_name": folder.name,
                    "cookie_db": cookie_db
                })

    return profiles


def count_chromium_cookies(cookie_db):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db = Path(temp_dir) / "Cookies"

        shutil.copy2(cookie_db, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT host_key, COUNT(*)
            FROM cookies
            GROUP BY host_key
            ORDER BY COUNT(*) DESC
        """)

        results = cursor.fetchall()

        cursor.close()
        conn.close()

    return results


def count_firefox_cookies(cookie_db):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db = Path(temp_dir) / "cookies.sqlite"

        shutil.copy2(cookie_db, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT host, COUNT(*)
            FROM moz_cookies
            GROUP BY host
            ORDER BY COUNT(*) DESC
        """)

        results = cursor.fetchall()

        cursor.close()
        conn.close()

    return results


def extract_browser_cookies():
    findings = []

    for browser_name, browser_info in BROWSERS.items():

        try:
            if browser_info["type"] == "chromium":
                profiles = get_chromium_profiles(browser_info["path"])

                for profile in profiles:
                    cookies = count_chromium_cookies(
                        profile["cookie_db"]
                    )

                    for domain, count in cookies[:20]:
                        findings.append({
                            "browser": browser_name,
                            "profile": profile["profile_name"],
                            "domain": domain,
                            "cookie_count": count
                        })

            elif browser_info["type"] == "firefox":
                profiles = get_firefox_profiles(browser_info["path"])

                for profile in profiles:
                    cookies = count_firefox_cookies(
                        profile["cookie_db"]
                    )

                    for domain, count in cookies[:20]:
                        findings.append({
                            "browser": browser_name,
                            "profile": profile["profile_name"],
                            "domain": domain,
                            "cookie_count": count
                        })

        except Exception as e:
            findings.append({
                "browser": browser_name,
                "error": str(e)
            })

    return findings