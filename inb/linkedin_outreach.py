#!/usr/bin/env python3
"""
LinkedIn Outreach - Send Direct Messages to connections
Uses cookie-based auth for reliability. Get li_at cookie from browser.
Safe daily limit: 25 messages.
Note: Can only DM people you're connected with or open profiles.
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
import undetected_chromedriver as uc


# ============== CONFIGURATION ==============
DAILY_LIMIT = 25  # Safe limit for messages
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
    """Set up undetected Chrome WebDriver to bypass bot detection."""
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--log-level=3')
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=140)
    driver.set_page_load_timeout(120)
    driver.implicitly_wait(15)
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


def send_direct_message(driver, public_id, message, debug=False):
    """Send a direct message to a LinkedIn profile."""
    profile_url = f'https://www.linkedin.com/in/{public_id}/'
    
    try:
        driver.get(profile_url)
    except Exception as e:
        return f'page_load_error: {str(e)[:50]}'
    
    time.sleep(random.uniform(4, 6))
    
    # DEBUG: Check page state
    if debug:
        print(f"  [DEBUG] URL: {driver.current_url[:60]}...")
        print(f"  [DEBUG] Title: {driver.title[:50]}...")
    
    # Check if redirected to login or error
    if 'login' in driver.current_url or 'authwall' in driver.current_url:
        return 'session_expired'
    
    # Check if page loaded properly
    if driver.title in ['', 'www.linkedin.com', 'LinkedIn']:
        if debug:
            print(f"  [DEBUG] Page appears blocked, waiting...")
        time.sleep(4)
        driver.refresh()
        time.sleep(4)
    
    # Scroll to load content
    try:
        driver.execute_script("window.scrollBy(0, 200)")
    except:
        pass
    time.sleep(1.5)
    
    try:
        # DEBUG: List all buttons on page
        if debug:
            all_btns = driver.find_elements(By.TAG_NAME, 'button')
            print(f"  [DEBUG] Found {len(all_btns)} buttons on page")
            for btn in all_btns[:12]:
                txt = btn.text.strip().replace('\n', ' ')[:40]
                aria = (btn.get_attribute('aria-label') or '')[:40]
                print(f"    - Text: '{txt}' | Aria: '{aria}'")
        
        # Find Message button
        msg_button = None
        
        # Method 1: Message button with span text
        buttons = driver.find_elements(By.XPATH, '//button[.//span[text()="Message"]]')
        if buttons:
            msg_button = buttons[0]
        
        # Method 2: aria-label containing "message"
        if not msg_button:
            buttons = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "message") or contains(@aria-label, "Message")]')
            if buttons:
                msg_button = buttons[0]
        
        # Method 3: Check More menu for Message option
        if not msg_button:
            more_buttons = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "More")]')
            if not more_buttons:
                more_buttons = driver.find_elements(By.XPATH, '//button[.//span[text()="More"]]')
            
            if more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", more_buttons[0])
                    time.sleep(1)
                    menu_msg = driver.find_elements(By.XPATH, '//*[contains(@class, "dropdown")]//*[text()="Message"]/ancestor::*[1]')
                    if menu_msg:
                        driver.execute_script("arguments[0].click();", menu_msg[0])
                        time.sleep(1)
                        return _send_message_in_modal(driver, message)
                except:
                    pass
        
        if not msg_button:
            # Check if we can connect instead
            connect_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="Connect"]]')
            if connect_btns:
                return 'not_connected'
            return 'no_message_button'
        
        # Click Message button
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", msg_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", msg_button)
        except Exception as e:
            return f'click_error: {str(e)[:50]}'
        
        time.sleep(1.5)
        return _send_message_in_modal(driver, message)
            
    except Exception as e:
        return f'error: {str(e)[:80]}'


def _send_message_in_modal(driver, message):
    """Type and send message in the message modal/composer."""
    try:
        time.sleep(1)
        
        # Find the message input area
        msg_box = None
        
        # Method 1: contenteditable div (LinkedIn's rich text editor)
        msg_boxes = driver.find_elements(By.XPATH, '//div[contains(@class, "msg-form__contenteditable")]')
        if msg_boxes:
            msg_box = msg_boxes[0]
        
        # Method 2: Any contenteditable in message form
        if not msg_box:
            msg_boxes = driver.find_elements(By.XPATH, '//div[@contenteditable="true" and contains(@class, "msg")]')
            if msg_boxes:
                msg_box = msg_boxes[0]
        
        # Method 3: Textarea fallback
        if not msg_box:
            msg_boxes = driver.find_elements(By.XPATH, '//textarea[contains(@name, "message") or contains(@class, "msg")]')
            if msg_boxes:
                msg_box = msg_boxes[0]
        
        # Method 4: Any contenteditable div in the modal
        if not msg_box:
            msg_boxes = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
            if msg_boxes:
                msg_box = msg_boxes[-1]  # Usually the last one is the composer
        
        if not msg_box:
            return 'no_message_box'
        
        # Click to focus and type message
        msg_box.click()
        time.sleep(0.3)
        msg_box.send_keys(message)
        time.sleep(0.5)
        
        # Find and click Send button
        send_btn = None
        
        # Method 1: Send button with aria-label
        send_btns = driver.find_elements(By.XPATH, '//button[contains(@aria-label, "Send")]')
        if send_btns:
            send_btn = send_btns[0]
        
        # Method 2: Send button text
        if not send_btn:
            send_btns = driver.find_elements(By.XPATH, '//button[.//span[text()="Send"]]')
            if send_btns:
                send_btn = send_btns[0]
        
        # Method 3: Button with type submit in message form
        if not send_btn:
            send_btns = driver.find_elements(By.XPATH, '//form[contains(@class, "msg")]//button[@type="submit"]')
            if send_btns:
                send_btn = send_btns[0]
        
        if not send_btn:
            return 'no_send_button'
        
        driver.execute_script("arguments[0].click();", send_btn)
        time.sleep(1)
        
        return 'sent'
        
    except Exception as e:
        return f'modal_error: {str(e)[:50]}'


def main():
    parser = argparse.ArgumentParser(description='LinkedIn Outreach - Send Direct Messages')
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
    print("🔗 LINKEDIN OUTREACH (Direct Messages)")
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
                result = send_direct_message(driver, public_id, args.message, debug=args.debug)
            except Exception as e:
                result = f'browser_error: {str(e)[:50]}'
            
            if result == 'sent':
                print(f"  ✅ Message sent!")
                success_count += 1
                increment_quota()
                update_excel_status(excel_path, df, row_index, 'sent', datetime.now().isoformat())
            elif result == 'not_connected':
                print(f"  ⚠️ Not connected - can't DM (need to connect first)")
                update_excel_status(excel_path, df, row_index, 'not_connected', '')
            elif result == 'session_expired':
                print(f"  ❌ Session expired - stopping")
                break
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
