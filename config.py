"""
Configuration for the Reddit API proxy bot.

This mirrors the approach Redlib (https://github.com/redlib-org/redlib) documents
in its own README: it spoofs the OAuth "installed_client" flow used by the
official Reddit Android app to obtain anonymous, account-less bearer tokens,
then talks to oauth.reddit.com using headers shaped like the real app. When
that path is unavailable, it falls back to Reddit's public, unauthenticated
*.json endpoints on www.reddit.com and old.reddit.com.

IMPORTANT — read before deploying:
  * The client_id below is the historical PUBLIC identifier used by the
    official Reddit Android app for logged-out/"installed client" sessions
    (the same one Redlib's maintainer documented sniffing via mitmproxy).
    It is not a secret and needs no login. Reddit periodically rotates or
    blocks these. If token requests start failing with 400/401, you'll need
    to capture a fresh one yourself (mitmproxy against the real app) or pull
    the current value from Redlib's own src/client.rs, and drop it into
    ANDROID_CLIENT_IDS below.
  * This is an "approximate" reimplementation as requested — it copies
    Redlib's strategy (spoofed installed-client OAuth + 24h refresh +
    header mimicking + domain fallback), not its exact byte-for-byte
    request/response handling.
  * Running high-volume automated scraping against Reddit may run against
    Reddit's Terms of Service / API terms depending on how you use it —
    that's on you to review for your use case.
"""

import random

# --- OAuth "installed client" identities ------------------------------------
# device_id is regenerated once per process (random UUID4) -- matches what the
# real app does for anonymous/logged-out sessions (one device id per install).

ANDROID_CLIENT_IDS = [
    "ohXpoqrZYub1kg",  # historical public client_id of the official Android app
    # Add more here (e.g. from other open-source Android Reddit clients) to
    # give the rotation logic somewhere to go if one gets blocked.
]

ANDROID_APP_VERSIONS = [
    "Version 2024.18.0/Build 1242708",
    "Version 2024.21.0/Build 1254893",
    "Version 2024.24.1/Build 1267511",
]

ANDROID_OS_STRINGS = ["Android 12", "Android 13", "Android 14"]

ANDROID_DEVICES = [
    "samsung SM-G991B",
    "samsung SM-A536B",
    "Google Pixel 7",
    "OnePlus CPH2449",
]


def random_android_user_agent() -> str:
    """Build a User-Agent shaped like the real Reddit app's:
    Reddit/<version>/<android ver> (<device>)
    """
    version = random.choice(ANDROID_APP_VERSIONS)
    os_ver = random.choice(ANDROID_OS_STRINGS)
    device = random.choice(ANDROID_DEVICES)
    return f"Reddit/{version}/{os_ver} ({device})"


# --- Fallback (unauthenticated) desktop UAs ---------------------------------
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# --- Endpoint tiers ----------------------------------------------------------
# Order = fallback priority. The client walks down this list whenever a tier
# fails outright (transport error / persistent 403 / exhausted retries).
OAUTH_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

FALLBACK_TIERS = [
    {"name": "oauth", "base": "https://oauth.reddit.com", "auth": True},
    {"name": "www-json", "base": "https://www.reddit.com", "auth": False},
    {"name": "old-json", "base": "https://old.reddit.com", "auth": False},
]

TOKEN_LIFETIME_SECONDS = 24 * 60 * 60  # Redlib refreshes every 24h
TOKEN_SAFETY_MARGIN = 60 * 5  # refresh 5 min before actual expiry

MAX_RETRIES_PER_TIER = 3
BACKOFF_BASE_SECONDS = 0.75
REQUEST_TIMEOUT = 10.0

CACHE_TTL_SECONDS = 10  # short-lived cache to absorb bursts of identical calls
CACHE_STALE_MAX_SECONDS = 600  # serve-stale-on-total-failure window
