#!/usr/bin/env python3
"""
simulate_attacks.py
===================
Run directly from your terminal to simulate real HTTP attacks against the
running backend. This is more realistic than the API-based simulation because
it sends ACTUAL HTTP requests through the login endpoint.

Usage:
    python scripts/simulate_attacks.py --mode brute    # brute force
    python scripts/simulate_attacks.py --mode sqli     # sql injection
    python scripts/simulate_attacks.py --mode ddos     # high rate
    python scripts/simulate_attacks.py --mode all      # everything
    python scripts/simulate_attacks.py --mode normal   # normal baseline

Requirements: pip install requests
"""

import argparse
import random
import time
import threading
import sys
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"

# ── Color output ──────────────────────────────────────────────────────────────
class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

def log(msg, color=C.CYAN):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{C.RESET}")

# ── Attack payloads ───────────────────────────────────────────────────────────
SQLI_PAYLOADS = [
    ("admin' OR '1'='1--",          "anything"),
    ("' UNION SELECT * FROM users--", "pass"),
    ("'; DROP TABLE users--",         "x"),
    ("admin'--",                      "pass"),
    ("' OR 1=1#",                     "pass"),
    ("\" OR \"\"=\"",                 "pass"),
    ("admin') OR ('1'='1",           "pass"),
    ("SLEEP(5)--",                    "x"),
]

XSS_PAYLOADS = [
    ("<script>alert('xss')</script>",           "pass"),
    ("<img src=x onerror=alert(1)>",             "pass"),
    ("javascript:alert(document.cookie)",        "pass"),
    ("<svg onload=alert(1)>",                    "pass"),
]

COMMON_PASSWORDS = [
    "password", "123456", "admin", "letmein", "qwerty",
    "pass123", "welcome", "monkey", "dragon", "master",
    "sunshine", "princess", "iloveyou", "admin123", "test",
]

NORMAL_USERS = [
    ("alice",   "alice_pass"),
    ("bob",     "bob_secure"),
    ("admin",   "admin123"),
    ("alice",   "wrong_pass"),
    ("charlie", "notauser"),
]

FAKE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "sqlmap/1.7.8#stable (https://sqlmap.org)",
    "python-requests/2.31.0",
    "Nikto/2.1.6",
    "curl/7.88.1",
    "masscan/1.0",
]


def post_login(username: str, password: str, ua: str = None, verbose: bool = True) -> dict:
    """Send one login request and return parsed response."""
    headers = {"User-Agent": ua or random.choice(FAKE_USER_AGENTS)}
    try:
        r = requests.post(LOGIN_URL, json={"username": username, "password": password},
                          headers=headers, timeout=5)
        data = r.json()
        if verbose:
            sec  = data.get("security", {})
            sev  = sec.get("severity", "low")
            atk  = sec.get("attack_type", "none")
            risk = sec.get("risk_score", 0)
            ok   = data.get("success", False)

            color = C.RED if sev in ("critical", "high") else C.YELLOW if sev == "medium" else C.GREEN
            icon  = "✅" if ok else "❌"
            log(
                f"{icon} user={username!r:25} attack={atk:20} sev={sev:8} risk={risk:.2f}",
                color
            )
        return data
    except requests.exceptions.ConnectionError:
        log("❌ Cannot connect to backend at " + BASE_URL, C.RED)
        log("   Make sure the backend is running: uvicorn app.main:app --reload", C.YELLOW)
        sys.exit(1)
    except Exception as e:
        log(f"Request failed: {e}", C.RED)
        return {}


# ── Simulation modes ──────────────────────────────────────────────────────────
def sim_brute_force(target="admin", attempts=25):
    log(f"🔨 BRUTE FORCE: {attempts} attempts against '{target}'", C.RED + C.BOLD)
    ua = "python-requests/2.31.0"
    for i in range(attempts):
        pw = random.choice(COMMON_PASSWORDS)
        post_login(target, pw, ua=ua)
        time.sleep(0.15)  # Fast but not instant
    log(f"✓ Brute force complete ({attempts} attempts)", C.GREEN)


def sim_sqli(attempts=None):
    payloads = attempts or SQLI_PAYLOADS
    log(f"💉 SQL INJECTION: {len(payloads)} payloads", C.RED + C.BOLD)
    for user, pw in payloads:
        post_login(user, pw, ua="sqlmap/1.7.8#stable")
        time.sleep(0.3)
    log(f"✓ SQLi simulation complete", C.GREEN)


def sim_xss():
    log(f"📜 XSS: {len(XSS_PAYLOADS)} payloads", C.YELLOW + C.BOLD)
    for user, pw in XSS_PAYLOADS:
        post_login(user, pw, ua="Mozilla/5.0")
        time.sleep(0.2)
    log(f"✓ XSS simulation complete", C.GREEN)


def sim_ddos(total=80, threads=10):
    log(f"🌊 DDoS: {total} requests across {threads} threads", C.RED + C.BOLD)
    lock   = threading.Lock()
    count  = [0]

    def worker():
        while True:
            with lock:
                if count[0] >= total:
                    break
                count[0] += 1
                n = count[0]
            post_login(f"user{random.randint(1,20)}", "pass", verbose=(n % 10 == 0))
            time.sleep(0.05)

    ts = [threading.Thread(target=worker) for _ in range(threads)]
    for t in ts: t.start()
    for t in ts: t.join()
    log(f"✓ DDoS simulation complete", C.GREEN)


def sim_normal(events=30):
    log(f"✅ NORMAL TRAFFIC: {events} events", C.GREEN + C.BOLD)
    for _ in range(events):
        user, pw = random.choice(NORMAL_USERS)
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        post_login(user, pw, ua=ua)
        time.sleep(random.uniform(0.3, 1.2))
    log(f"✓ Normal traffic complete", C.GREEN)


def sim_all():
    log("🎯 FULL ATTACK SCENARIO", C.CYAN + C.BOLD)
    log("Step 1/5: Normal baseline traffic (20 events)...", C.CYAN)
    sim_normal(20)
    time.sleep(1)
    log("Step 2/5: Brute force attack (15 attempts)...", C.CYAN)
    sim_brute_force(attempts=15)
    time.sleep(1)
    log("Step 3/5: SQL injection (all payloads)...", C.CYAN)
    sim_sqli()
    time.sleep(1)
    log("Step 4/5: XSS payloads...", C.CYAN)
    sim_xss()
    time.sleep(1)
    log("Step 5/5: DDoS burst (60 requests, 8 threads)...", C.CYAN)
    sim_ddos(total=60, threads=8)
    log("🎉 Full scenario complete! Check the dashboard.", C.GREEN + C.BOLD)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Security Monitor - Attack Simulator")
    parser.add_argument(
        "--mode", default="all",
        choices=["brute", "sqli", "xss", "ddos", "normal", "all"],
        help="Attack type to simulate"
    )
    parser.add_argument("--url",      default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--attempts", type=int, default=20,            help="Number of attempts")
    args = parser.parse_args()

    BASE_URL  = args.url
    LOGIN_URL = f"{BASE_URL}/api/auth/login"

    print(f"\n{C.CYAN}{C.BOLD}{'='*60}")
    print(" AI Security Monitor — Attack Simulator")
    print(f" Target: {LOGIN_URL}")
    print(f"{'='*60}{C.RESET}\n")

    # Health check
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=3)
        log(f"Backend healthy: {r.json()}", C.GREEN)
    except:
        log("Cannot reach backend. Is it running?", C.RED)
        sys.exit(1)

    print()
    if   args.mode == "brute":  sim_brute_force(attempts=args.attempts)
    elif args.mode == "sqli":   sim_sqli()
    elif args.mode == "xss":    sim_xss()
    elif args.mode == "ddos":   sim_ddos(total=args.attempts)
    elif args.mode == "normal": sim_normal(events=args.attempts)
    elif args.mode == "all":    sim_all()
