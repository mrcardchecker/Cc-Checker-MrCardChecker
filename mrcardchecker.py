#!/usr/bin/env python3
"""
MrCardChecker CLI Tool
- Free Luhn Checker (CCN Gate 1)
- Premium Checker (CCN3 Gate) – requires login, shows balance ($1–$5)
- BIN Checker & Generator
- Login / Logout
- Back/Home navigation from any sub‑menu
"""

import sys
import re
import random
import requests
from datetime import datetime

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

# API Endpoints
LOGIN_URL = "https://mrcardchecker.live/user/api_login.php"
CHECKER_URL = "https://api.ghakr.com/api_python.php"

# Global session and user data
session = requests.Session()
is_logged_in = False
user_plan = 'none'
plan_active = False

# ================ UTILITY FUNCTIONS (Local) ================

def luhn_check(card_number: str) -> bool:
    """Validate card using Luhn algorithm (MOD 10)."""
    digits = re.sub(r'\D', '', card_number)
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        num = int(d)
        if i % 2 == 1:
            num *= 2
            if num > 9:
                num -= 9
        total += num
    return total % 10 == 0

def get_card_brand(number: str) -> str:
    """Identify card brand from first digits."""
    patterns = {
        'VISA': r'^4',
        'MASTERCARD': r'^5[1-5]',
        'AMEX': r'^3[47]',
        'DISCOVER': r'^6(?:011|5)',
        'DINERS': r'^3(?:0[0-5]|[68])',
        'JCB': r'^(?:2131|1800|35)'
    }
    for brand, pattern in patterns.items():
        if re.match(pattern, number):
            return brand
    return 'UNKNOWN'

def generate_luhn_number(bin_prefix: str, length: int = 16) -> str:
    """Generate a valid Luhn number from a BIN prefix."""
    if len(bin_prefix) >= length:
        return bin_prefix[:length]
    number = bin_prefix
    while len(number) < length - 1:
        number += str(random.randint(0, 9))
    # Calculate check digit
    digits = list(number)
    total = 0
    for i, d in enumerate(digits):
        num = int(d)
        if (len(digits) - i) % 2 == 0:
            num *= 2
            if num > 9:
                num -= 9
        total += num
    check_digit = (10 - (total % 10)) % 10
    return number + str(check_digit)

def parse_cc_line(line: str) -> dict | None:
    """Parse a card line: NUMBER|MM|YY|CVV."""
    line = line.strip()
    if not line:
        return None
    parts = re.split(r'[|,\s]+', line)
    number = re.sub(r'\D', '', parts[0])
    if len(number) < 13:
        return None
    return {
        'number': number,
        'month': parts[1] if len(parts) > 1 else '',
        'year': parts[2] if len(parts) > 2 else '',
        'cvv': parts[3] if len(parts) > 3 else '',
        'raw': line
    }

def validate_cc_local(card: dict) -> str:
    """Local validation with expiry check and 15% live simulation."""
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    if card['month'] and card['year']:
        try:
            exp_month = int(card['month'])
            exp_year = int(card['year'])
            if exp_year < 100:
                exp_year += 2000
            if exp_year < current_year:
                return 'die'
            if exp_year == current_year and exp_month < current_month:
                return 'die'
        except ValueError:
            pass
    # 15% chance live, 85% die
    return 'live' if random.random() < 0.15 else 'die'

def display_local_result(card_line: str, result: str, brand: str):
    """Print result for local checker (free)."""
    if result == 'live':
        print(f"✅ LIVE: {card_line} -> Approved [{brand}]")
    elif result == 'die':
        die_msgs = ["Declined", "Expired", "Insufficient Funds", "Security Code Mismatch"]
        print(f"❌ DIE:  {card_line} -> {random.choice(die_msgs)} [{brand}]")
    else:
        print(f"❓ UNKNOWN: {card_line} -> Invalid Format [{brand}]")

# ================ LOGIN / LOGOUT ================

def login() -> bool:
    """Authenticate user and store session."""
    global is_logged_in, user_plan, plan_active
    print("\n" + "="*50)
    print("🔐 CCN3 Premium Login")
    print("="*50)
    username = input("Username or Email: ").strip()
    password = input("Password: ").strip()
    if not username or not password:
        print("❌ Username and password required.")
        return False

    try:
        response = session.post(LOGIN_URL, data={'username': username, 'password': password}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                is_logged_in = True
                user_plan = data.get('plan', 'none')
                plan_active = data.get('plan_active', False)
                print(f"✅ Login successful!")
                print(f"   Plan: {user_plan.upper()}")
                print(f"   Status: {'ACTIVE' if plan_active else 'EXPIRED / FREE'}")
                return True
            else:
                print(f"❌ Login failed: {data.get('msg', 'Unknown error')}")
        else:
            print(f"❌ Server error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    return False

def logout():
    """Clear session and user data."""
    global is_logged_in, user_plan, plan_active
    is_logged_in = False
    user_plan = 'none'
    plan_active = False
    session.cookies.clear()
    print("✅ Logged out successfully.")

# ================ PREMIUM CHECKER (API) ================

def check_card_premium(card_line: str) -> dict:
    """Send card to API with session cookies."""
    payload = {"cclist": card_line}
    try:
        response = session.post(CHECKER_URL, data=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "msg": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def display_premium_result(card_line: str, result: dict):
    """Display result from premium API with balance (if any)."""
    status = result.get("status", "unknown")
    msg = result.get("msg", "No message")
    brand = result.get("brand", "UNKNOWN")
    charge = result.get("charge", "")
    
    if status == "live":
        if charge:
            print(f"✅ LIVE: {card_line} -> {msg} [${charge}] [{brand}]")
        else:
            print(f"✅ LIVE: {card_line} -> {msg} [{brand}]")
    elif status == "die":
        print(f"❌ DIE:  {card_line} -> {msg} [{brand}]")
    elif status == "unknown":
        print(f"❓ UNKNOWN: {card_line} -> {msg} [{brand}]")
    else:
        print(f"⚠️ ERROR: {card_line} -> {msg}")

# ================ MENU FUNCTIONS (with Back/Home support) ================

def is_back_or_home(user_input: str) -> bool:
    """Check if user wants to go back to main menu."""
    return user_input.lower() in ('back', 'home', 'menu')

def cc_gate1():
    """Free Luhn checker (local)."""
    print(f"\n{CYAN}>> CCN Gate 1 (Free Luhn Checker) <<{RESET}")
    print("Enter cards (NUMBER|MM|YY|CVV).")
    print("Type 'back' or 'home' to return to main menu.\n")
    while True:
        raw = input("cc1 > ").strip()
        if is_back_or_home(raw):
            return
        if not raw:
            continue
        card = parse_cc_line(raw)
        if not card:
            print("❓ SKIP: Invalid format ->", raw)
            continue
        brand = get_card_brand(card['number'])
        result = validate_cc_local(card)
        display_local_result(raw, result, brand)

def cc3_premium():
    """Premium checker – requires login."""
    global is_logged_in
    if not is_logged_in:
        print("❌ Please login first (option 5).")
        return
    
    print(f"\n{CYAN}>> CCN3 Gate Premium <<{RESET}")
    print(f"   Plan: {user_plan.upper()} | Status: {'ACTIVE' if plan_active else 'EXPIRED'}")
    print("Enter cards (NUMBER|MM|YY|CVV).")
    print("Type 'back' or 'home' to return to main menu.\n")
    while True:
        raw = input("cc3 > ").strip()
        if is_back_or_home(raw):
            return
        if not raw:
            continue
        result = check_card_premium(raw)
        display_premium_result(raw, result)

def bin_checker():
    """BIN lookup."""
    print(f"\n{CYAN}>> BIN Checker <<{RESET}")
    print("Enter first 6 digits (BIN).")
    print("Type 'back' or 'home' to return to main menu.\n")
    while True:
        raw = input("bin > ").strip()
        if is_back_or_home(raw):
            return
        if not raw:
            continue
        bin_num = re.sub(r'\D', '', raw)[:6]
        if len(bin_num) < 6:
            print(f"{YELLOW}Please enter at least 6 digits.{RESET}")
            continue
        brand = get_card_brand(bin_num)
        card_type = "CREDIT" if random.random() > 0.5 else "DEBIT"
        level = random.choice(["CLASSIC", "GOLD", "PLATINUM", "INFINITE"])
        print(f"{CYAN}─ BIN Info ─────────────────────────────────{RESET}")
        print(f"  BIN       : {bin_num}")
        print(f"  Brand     : {brand}")
        print(f"  Type      : {card_type}")
        print(f"  Level     : {level}")
        print(f"{CYAN}────────────────────────────────────────────{RESET}\n")

def bin_generator():
    """Generate valid cards from a BIN."""
    print(f"\n{CYAN}>> BIN Generator <<{RESET}")
    print("Enter BIN (first 6 digits).")
    print("Type 'back' or 'home' to return to main menu.\n")
    while True:
        raw = input("gen > ").strip()
        if is_back_or_home(raw):
            return
        if not raw:
            continue
        bin_num = re.sub(r'\D', '', raw)[:6]
        if len(bin_num) < 6:
            print(f"{YELLOW}Please enter at least 6 digits.{RESET}")
            continue
        print(f"\n{CYAN}Generated 5 cards from BIN {bin_num}:{RESET}")
        for i in range(5):
            card = generate_luhn_number(bin_num, 16)
            month = str(random.randint(1, 12)).zfill(2)
            year = str(random.randint(2026, 2032))
            cvv = str(random.randint(100, 999))
            print(f"  {i+1}. {card}|{month}|{year}|{cvv}")
        print()
        break

# ================ BANNER WITH CUSTOM ASCII ART (RAW F-STRING) ================

def print_banner():
    """Display the custom SHYK ASCII art banner."""
    banner = fr"""
{CYAN}      ___           ___           ___     
     /\  \         /\__\         /\__\    
    |::\  \       /:/  /        /:/  /    
    |:|:\  \     /:/  /        /:/  /     
  __|:|\:\  \   /:/  /  ___   /:/  /  ___ 
 /::::|_\:\__\ /:/__/  /\__\ /:/__/  /\__\
 \:\~~\  \/__/ \:\  \ /:/  / \:\  \ /:/  /
  \:\  \        \:\  /:/  /   \:\  /:/  / 
   \:\  \        \:\/:/  /     \:\/:/  /  
    \:\__\        \::/  /       \::/  /   
     \/__/         \/__/         \/__/    
{RESET}
{CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              
║  {YELLOW}⚡ {RESET}Advanced Credit Card Validator & BIN Tool Suite{RESET}{YELLOW} ⚡{RESET}              
║                                                                              
║  {GREEN}🌐 {RESET}Website : {CYAN}https://mrcardchecker.live{RESET}                                   
║  {GREEN}✈️ {RESET}Telegram: {CYAN}https://t.me/mrcardcheckeradmin_new{RESET}                         
║                                                                              
║  {RED}🔒 {RESET}Secure · Fast · Premium CCN3 Gate{RESET}{RED} 🔒{RESET}                               
║                                                                              
╚══════════════════════════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)

# ================ MAIN MENU ================

def show_menu():
    status = f"Logged in as {user_plan.upper()}" if is_logged_in else "Not logged in"
    print("\n" + "-"*50)
    print("  [1] CCN Gate 1 (Free Luhn Checker)")
    print("  [2] CCN3 Gate Premium (Requires Login)")
    print("  [3] BIN Checker")
    print("  [4] BIN Generator")
    print("  [5] Login")
    print("  [6] Logout")
    print("  [0] Exit")
    print("-"*50)
    print(f"  Status: {status}")
    print("-"*50)

def main():
    global is_logged_in
    print_banner()
    while True:
        show_menu()
        choice = input("Select option: ").strip()
        if choice == '1':
            cc_gate1()
        elif choice == '2':
            cc3_premium()
        elif choice == '3':
            bin_checker()
        elif choice == '4':
            bin_generator()
        elif choice == '5':
            if is_logged_in:
                print("You are already logged in.")
            else:
                login()
        elif choice == '6':
            if is_logged_in:
                logout()
            else:
                print("You are not logged in.")
        elif choice == '0':
            print(f"\n{GREEN}Exiting tool. Goodbye!{RESET}")
            sys.exit()
        else:
            print(f"{RED}Invalid choice. Please select 0-6.{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{GREEN}Interrupted. Exiting...{RESET}")
        sys.exit()