#!/usr/bin/env python3
"""
LinkedIn Outreach - Send connection requests with message (cold DM)
Uses cookie-based auth for reliability. Get li_at cookie from browser.
Safe daily limit: 25 connection requests with messages.
"""

import os
import sys
import time
import json
import argparse
import pandas as pd
import re
import random
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# ============== CONFIGURATION ==============
DAILY_LIMIT = 25  # Safe limit for connection requests with messages
QUOTA_FILE = 'linkedin_quota.json'

# Hardcoded resume link and message
RESUME_LINK = "https://drive.google.com/file/d/14pEaC7-svetAUzXRZYsnM09cW3VzH2r2/view"
DEFAULT_MESSAGE = f"""Hi! I'm Surya, a passionate Software Engineer with expertise in Full Stack, AI/ML, and LLMs.

I'm actively looking for SDE/Intern roles and would love to connect! If there are any openings, I'd really appreciate a referral.

Resume: {RESUME_LINK}

Thank you! 🙏"""
# ===========================================


def load_quota():
    """Load today's usage quota."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    quota_path = os.path.join(script_dir, QUOTA_FILE)
    
    today = date.today().isoformat()
    
    if os.path.exists(quota_path):
        with open(quota_path, 'r') as f:
            quota = json.load(f)
        if quota.get('date') != today:
            quota = {'date': today, 'sent': 0}
    else:
        quota = {'date': today, 'sent': 0}
    
    return quota


def save_quota(quota):
    """Save current quota."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    quota_path = os.path.join(script_dir, QUOTA_FILE)
    with open(quota_path, 'w') as f:
        json.dump(quota, f)


def get_remaining_quota():
    """Get how many messages we can still send today."""
    quota = load_quota()
    return max(0, DAILY_LIMIT - quota['sent'])


def increment_quota():
    """Increment the sent counter."""
    quota = load_quota()
    quota['sent'] += 1
    save_quota(quota)
    return quota['sent']


def extract_public_id(linkedin_url):
    """Extract public_id from LinkedIn URL."""
    if not linkedin_url or pd.isna(linkedin_url):
        return None
    match = re.search(r'linkedin\.com/in/([^/?]+)', str(linkedin_url))
    return match.group(1) if match else None


def load_profiles_from_excel(excel_path, limit=20):
    """Load profiles from Excel file that haven't been contacted yet."""
    df = pd.read_excel(excel_path)
    
    # Filter rows where Status is empty/NaN (not contacted yet)
    unsent = df[df['Status'].isna() | (df['Status'] == '')]
    
    profiles = []
    for _, row in unsent.head(limit).iterrows():
        public_id = extract_public_id(row.get('Linkedin URL', ''))
        if public_id:
            profiles.append({
                'name': row.get('Name', 'Unknown'),
                'public_id': public_id,
                'company': row.get('Company Name', 'N/A'),
                'linkedin_url': row.get('Linkedin URL', ''),
                'row_index': row.name
            })
    
    return df, profiles


def update_excel_status(excel_path, df, row_index, status, delivered=''):
    """Update the Status and Delivered columns in Excel."""
    df.at[row_index, 'Status'] = status
    if delivered:
        df.at[row_index, 'Delivered'] = delivered
    df.to_excel(excel_path, index=False)


def setup_driver(headless=True):
    """Set up Chrome WebDriver."""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    # Additional stability options
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-accelerated-2d-canvas')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--disable-infobars')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--log-level=3')  # Suppress most logs
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('prefs', {
        'profile.default_content_setting_values.notifications': 2,
        'credentials_enable_service': False,
        'profile.password_manager_enabled': False
    })
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(120)  # 2 minutes
    driver.implicitly_wait(15)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def login_with_cookie(driver, li_at_cookie):
    """Login using li_at cookie (most reliable method)."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries}...")
            # First go to LinkedIn to set the domain
            driver.get('https://www.linkedin.com')
            time.sleep(3)
            
            # Add the li_at cookie
            driver.add_cookie({
                'name': 'li_at',
                'value': li_at_cookie,
                'domain': '.linkedin.com',
                'path': '/',
                'secure': True
            })
            
            # Refresh to apply cookie
            driver.get('https://www.linkedin.com/feed/')
            time.sleep(5)
            
            # Check if logged in
            current_url = driver.current_url
            if 'feed' in current_url or 'mynetwork' in current_url or '/in/' in current_url:
                return True
            if 'login' in current_url or 'checkpoint' in current_url:
                print(f"   Login page detected, cookie may be expired")
                return False
            return True
        except Exception as e:
            print(f"   Attempt {attempt + 1} failed: {str(e)[:50]}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return False
    return False


def login_with_password(driver, email, password):
    """Fallback login with email/password."""
    driver.get('https://www.linkedin.com/login')
    time.sleep(2)
    
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))
        )
        email_field.clear()
        email_field.send_keys(email)
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.clear()
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()
        
        time.sleep(3)
        
        if 'checkpoint' in driver.current_url or 'challenge' in driver.current_url:
            print("⚠️ Security challenge - use cookie auth instead")
            return False
            
        return 'feed' in driver.current_url or 'mynetwork' in driver.current_url or 'in/' in driver.current_url
        
    except Exception as e:
        print(f"Login error: {e}")
        return False


def send_connection_with_message(driver, public_id, message, debug=False):
    """Send connection request with a personalized message (cold DM)."""
    profile_url = f'https://www.linkedin.com/in/{public_id}/'
    
    try:
        driver.get(profile_url)
    except Exception as e:
        return f'page_load_error: {str(e)[:50]}'
    
    time.sleep(random.uniform(4, 6))  # Increased wait
    
    # DEBUG: Check page state
    if debug:
        print(f"  [DEBUG] URL: {driver.current_url[:60]}...")
        print(f"  [DEBUG] Title: {driver.title[:50]}...")
    
    # Check if redirected to login or error
    if 'login' in driver.current_url or 'authwall' in driver.current_url:
        return 'session_expired'
    if 'error' in driver.title.lower() or driver.title == '':
        # Wait more and retry
        time.sleep(3)
        driver.refresh()
        time.sleep(4)
    
    # Scroll to load content
    try:
        driver.execute_script("window.scrollBy(0, 300)")
    except:
        pass
    time.sleep(1.5)
    
    try:
        connect_button = None
        
        # DEBUG: List all buttons on page
        if debug:
            all_btns = driver.find_elements(By.TAG_NAME, 'button')
            print(f"  [DEBUG] Found {len(all_btns)} buttons on page")
            for btn in all_btns[:15]:  # First 15 buttons
                txt = btn.text.strip().replace('\n', ' ')[:40]
                aria = (btn.get_attribute('aria-label') or '')[:40]
                print(f"    - Text: '{txt}' | Aria: '{aria}'")
        
        # Check if already connected first
        if driver.find_elements(By.XPATH, '//button[.//span[text()="Message"]]'):
            return 'already_connected'
        if driver.find_elements(By.XPATH, '//button[.//span[text()="Pending"]]'):
            return 'pending'
        
        # Method 1: Direct Connect button with aria-label containing "Invite"
        buttons = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Invite")]')
        if buttons:
            connect_button = buttons[0]
        
        # Method 2: Connect button with span text
        if not connect_button:
            buttons = driver.find_elements(By.XPATH, '//button[.//span[text()="Connect"]]')
            if buttons:
                connect_button = buttons[0]
        
        # Method 3: Any button containing "Connect" text
        if not connect_button:
            buttons = driver.find_elements(By.XPATH, '//button[contains(., "Connect")]')
            for btn in buttons:
                if 'connect' in btn.text.lower():
                    connect_button = btn
                    break
        
        # Method 4: Check More menu dropdown
        if not connect_button:
            more_buttons = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "More")]')
            if not more_buttons:
                more_buttons = driver.find_elements(By.XPATH, '//button[.//span[text()="More"]]')
            
            if more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", more_buttons[0])
                    time.sleep(1.5)
                    
                    # Find Connect in dropdown menu
                    menu_connect = driver.find_elements(By.XPATH, '//div[contains(@class, "dropdown")]//span[text()="Connect"]/ancestor::*[self::button or @role="menuitem" or @role="button"]')
                    if not menu_connect:
                        menu_connect = driver.find_elements(By.XPATH, '//*[contains(@class, "dropdown")]//*[text()="Connect"]/ancestor::*[1]')
                    
                    if menu_connect:
                        driver.execute_script("arguments[0].click();", menu_connect[0])
                        time.sleep(1)
                        return _handle_connect_modal(driver, message)
                except Exception as e:
                    pass  # Close dropdown and continue
        
        # Method 5: Look for primary action button
        if not connect_button:
            buttons = driver.find_elements(By.XPATH, '//div[contains(@class, "profile-action")]//button[contains(@class, "primary")]')
            for btn in buttons:
                if 'connect' in btn.text.lower() or 'connect' in (btn.get_attribute('aria-label') or '').lower():
                    connect_button = btn
                    break
        
        if not connect_button:
            # Last check for follow-only profiles
            if driver.find_elements(By.XPATH, '//button[.//span[text()="Follow"]]'):
                return 'follow_only'
            return 'no_connect_button'
        
        # Click Connect
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", connect_button)
        except Exception as e:
            return f'click_error: {str(e)[:50]}'
        time.sleep(1)
        
        return _handle_connect_modal(driver, message)
            
    except Exception as e:
        return f'error: {str(e)[:80]}'


def _handle_connect_modal(driver, message):
    """Handle the connection modal - add note with message."""
    try:
        time.sleep(1.5)
        
        # Look for "Add a note" button - multiple patterns
        add_note_btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Add a note")]')
        if not add_note_btns:
            add_note_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="Add a note"]]')
        if not add_note_btns:
            add_note_btns = driver.find_elements(By.XPATH, '//button[contains(., "Add a note")]')
        
        if add_note_btns and message:
            driver.execute_script("arguments[0].click();", add_note_btns[0])
            time.sleep(1)
            
            # Find textarea - multiple patterns
            textareas = driver.find_elements(By.XPATH, '//textarea[contains(@name, "message")]')
            if not textareas:
                textareas = driver.find_elements(By.XPATH, '//textarea[contains(@id, "custom-message")]')
            if not textareas:
                textareas = driver.find_elements(By.TAG_NAME, 'textarea')
            
            if textareas:
                textareas[0].clear()
                textareas[0].send_keys(message[:300])  # LinkedIn limit
                time.sleep(0.5)
        
        # Find and click Send - multiple patterns
        send_btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Send")]')
        if not send_btns:
            send_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="Send"]]')
        if not send_btns:
            send_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="Send now"]]')
        if not send_btns:
            send_btns = driver.find_elements(By.XPATH, '//button[contains(@class, "artdeco-button--primary")][.//span]')
        
        if send_btns:
            driver.execute_script("arguments[0].click();", send_btns[0])
            time.sleep(1)
            return 'sent'
        
        return 'modal_no_send'
        
    except Exception as e:
        try:
            dismiss = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Dismiss")]')
            if dismiss:
                dismiss[0].click()
        except:
            pass
        return f'modal_error: {str(e)[:50]}'


def main():
    parser = argparse.ArgumentParser(description='LinkedIn Outreach - Cold DM via Connection Request')
    parser.add_argument('--cookie', help='LinkedIn li_at cookie value (preferred)')
    parser.add_argument('--email', help='LinkedIn email (fallback)')
    parser.add_argument('--password', help='LinkedIn password (fallback)')
    parser.add_argument('--excel', default='linkedin-data.xlsx', help='Excel file with profiles')
    parser.add_argument('--limit', type=int, default=25, help='Max messages to send (respects daily quota)')
    parser.add_argument('--message', default='', help='Message to send (max 300 chars)')
    parser.add_argument('--resume', default='', help='Resume link to include in message')
    parser.add_argument('--headless', action='store_true', help='Run headless')
    parser.add_argument('--debug', action='store_true', help='Debug mode - show page buttons')
    
    args = parser.parse_args()
    
    # Check auth
    li_at = args.cookie or os.environ.get('LINKEDIN_COOKIE')
    if not li_at and not (args.email and args.password):
        print("❌ Need --cookie or (--email and --password)")
        sys.exit(1)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(script_dir, args.excel)
    
    # Check quota
    remaining = get_remaining_quota()
    quota = load_quota()
    
    print("=" * 60)
    print("🔗 LINKEDIN OUTREACH (Connection + Message)")
    print("=" * 60)
    print(f"📊 Daily Quota: {quota['sent']}/{DAILY_LIMIT} used, {remaining} remaining")
    print(f"📁 Excel: {args.excel}")
    print(f"🎯 Requested: {args.limit}")
    print()
    
    if remaining == 0:
        print("⛔ Daily quota exhausted! Try again tomorrow.")
        return
    
    # Limit by remaining quota
    effective_limit = min(args.limit, remaining)
    if effective_limit < args.limit:
        print(f"⚠️ Limiting to {effective_limit} due to daily quota")
    
    # Build message - use hardcoded default
    if not args.message:
        args.message = DEFAULT_MESSAGE
    
    # Trim to 300 chars (LinkedIn limit)
    if len(args.message) > 300:
        args.message = args.message[:297] + "..."
    
    print(f"💬 Message ({len(args.message)} chars):")
    print(f"   {args.message[:100]}...")
    print()
    
    try:
        # Load profiles
        print(f"📂 Loading profiles from Excel...")
        df, profiles = load_profiles_from_excel(excel_path, effective_limit)
        print(f"📋 Found {len(profiles)} profiles to contact\n")
        
        if not profiles:
            print("✅ No unsent profiles found. All done!")
            return
        
        # Setup browser
        print("🌐 Starting browser...")
        driver = setup_driver(headless=args.headless)
        
        # Login
        print("🔐 Authenticating...")
        if li_at:
            print("   Using cookie auth...")
            logged_in = login_with_cookie(driver, li_at)
        else:
            print("   Using password auth...")
            logged_in = login_with_password(driver, args.email, args.password)
        
        if not logged_in:
            print("❌ Authentication failed!")
            driver.quit()
            sys.exit(1)
        print("✅ Authenticated!\n")
        
        # Process profiles
        success_count = 0
        failure_count = 0
        start_time = time.time()
        
        for i, profile in enumerate(profiles, 1):
            # Check quota again
            if get_remaining_quota() == 0:
                print("\n⛔ Daily quota reached. Stopping.")
                break
            
            name = profile['name']
            public_id = profile['public_id']
            company = profile['company']
            row_index = profile['row_index']
            
            print(f"[{i}/{len(profiles)}] {name}")
            print(f"  🏢 {company}")
            print(f"  🔗 {public_id}")
            
            try:
                result = send_connection_with_message(driver, public_id, args.message, debug=args.debug)
            except Exception as e:
                result = f'browser_error: {str(e)[:50]}'
            
            if result == 'sent':
                print(f"  ✅ Message sent with connection request!")
                success_count += 1
                increment_quota()
                update_excel_status(excel_path, df, row_index, 'sent', datetime.now().isoformat())
            elif result == 'already_connected':
                print(f"  ℹ️ Already connected (can DM directly)")
                update_excel_status(excel_path, df, row_index, 'connected', '')
            elif result == 'pending':
                print(f"  ℹ️ Request already pending")
                update_excel_status(excel_path, df, row_index, 'pending', '')
            elif result == 'follow_only':
                print(f"  ⚠️ Can only follow (no connect option)")
                update_excel_status(excel_path, df, row_index, 'follow_only', '')
            else:
                print(f"  ❌ Failed: {result}")
                failure_count += 1
                update_excel_status(excel_path, df, row_index, 'failed', result[:50])
            
            # Random delay (5-12 seconds)
            if i < len(profiles) and get_remaining_quota() > 0:
                delay = random.uniform(5, 12)
                print(f"  ⏳ Waiting {delay:.1f}s...\n")
                time.sleep(delay)
        
        try:
            driver.quit()
        except:
            pass
        
        # Summary
        elapsed = time.time() - start_time
        final_quota = load_quota()
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"✅ Sent: {success_count}")
        print(f"❌ Failed: {failure_count}")
        print(f"📊 Daily usage: {final_quota['sent']}/{DAILY_LIMIT}")
        print(f"⏱️ Time: {elapsed:.1f}s")
        print(f"📁 Excel updated: {args.excel}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
