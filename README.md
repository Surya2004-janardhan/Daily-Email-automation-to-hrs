# 🚀 Job Application Automation

Automated job application system with **Email campaigns** and **LinkedIn outreach**. Uses AI-powered content variation and smart rate limiting to maximize reach while staying under platform limits.

## ✨ Features

### 📧 Email Automation
- **Google Sheets Integration**: Read/write HR contacts directly from Google Sheets
- **AI-Powered Email Variants**: Uses Groq LLM to generate 5 unique subject/body variations per run
- **Smart Batching**: Sends 50 emails per run (5 batches × 10 BCC recipients each)
- **Bounce Detection**: Verifies email delivery 20 mins after sending
- **Resume via Drive Link**: No attachments - uses Google Drive link for resume

### 🔗 LinkedIn Automation
- **Cookie-Based Auth**: Reliable long-term authentication (no 2FA challenges)
- **Cold DM via Connection Requests**: Sends personalized message with resume link
- **Excel-Based Profiles**: Reads 1800+ recruiter profiles from Excel file
- **Daily Quota Tracking**: Stays under 25 messages/day to avoid restrictions
- **Auto Status Updates**: Tracks sent/pending/failed in Excel

### 📬 Notifications
- Email notifications for success/failure of both systems
- Detailed logs with counts and errors

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS (Scheduled)                    │
├─────────────────────────────────┬───────────────────────────────┤
│        EMAIL SYSTEM             │       LINKEDIN SYSTEM          │
│   (8 AM & 8 PM UTC daily)       │      (10 AM UTC daily)         │
├─────────────────────────────────┼───────────────────────────────┤
│  Google Sheets → Groq LLM       │  Excel File → Selenium         │
│       ↓                         │       ↓                        │
│  Gmail SMTP (50 emails)         │  LinkedIn (20 messages)        │
│       ↓                         │       ↓                        │
│  Update Sheet + Notify          │  Update Excel + Notify         │
└─────────────────────────────────┴───────────────────────────────┘
```

## 📁 Project Structure

```
├── src/
│   └── index.js              # Main email orchestrator
├── scripts/
│   ├── phase1.js             # Load unsent emails from Google Sheets
│   ├── phase2.js             # Prepare batches of 10 emails
│   ├── phase3.js             # Send BCC emails via Gmail
│   ├── phase4.js             # Update sent status in Sheets
│   ├── phase5.js             # Verify email delivery (bounce check)
│   └── llm.js                # Groq LLM integration for variants
├── inb/
│   ├── linkedin_outreach.py  # LinkedIn automation script
│   ├── linkedin-data.xlsx    # 1800+ recruiter profiles
│   └── linkedin_quota.json   # Daily usage tracking
├── .github/workflows/
│   ├── daily-email.yml       # Email automation (8 AM/PM UTC)
│   ├── verify-delivery.yml   # Bounce check (after emails)
│   └── linkedin-automation.yml # LinkedIn (10 AM UTC)
└── package.json
```

## 🔧 Setup

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/email-automation-to-hrs.git
cd email-automation-to-hrs
npm install
```

### 2. Environment Variables

Create a `.env` file:

```env
# Gmail Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Groq API Key
GROQ_API_KEY=your-groq-api-key
```

### 3. Google Sheets Setup

1. Create a Google Sheet with columns: `email` (A) and `sent_status` (B)
2. Create a Google Cloud service account
3. Share the sheet with the service account email
4. Place the service account JSON file in the project root

### 4. Gmail App Password

1. Enable 2-Factor Authentication on Gmail
2. Go to Google Account → Security → App Passwords
3. Generate a new app password for "Mail"
4. Use this as `EMAIL_PASS`

### 5. Groq API Key

1. Sign up at [Groq Console](https://console.groq.com)
2. Create an API key
3. Add to `.env` as `GROQ_API_KEY`

## 🚀 Usage

### Run Locally

```bash
npm start
# or
node src/index.js
```

### What Happens Each Run

1. **Load**: Fetches unsent emails from Google Sheets (first 50)
2. **Generate**: Calls Groq LLM to create 5 unique subject/body variants
3. **Send**: Sends 5 batches of 10 BCC emails (each with different variant)
4. **Update**: Marks all sent emails as "email sent" in the sheet
5. **Notify**: Sends success/failure report to your personal email

### GitHub Actions (Automated)

The workflow runs automatically at:
- 🌅 8:00 AM UTC daily
- 🌆 8:00 PM UTC daily

Manual trigger available via GitHub Actions → Run workflow

## 📊 Phases Explained

| Phase | File | Description |
|-------|------|-------------|
| 1 | `phase1.js` | Load unsent emails from Google Sheets |
| 2 | `phase2.js` | Split 50 emails into 5 batches of 10 |
| 3 | `phase3.js` | Send BCC email + success/failure notification |
| 4 | `phase4.js` | Update "email sent" status in Sheets |
| LLM | `llm.js` | Generate 5 subject/body variants via Groq |

## 🔐 GitHub Secrets Required

For GitHub Actions automation, add these secrets:

| Secret | Description |
|--------|-------------|
| `EMAIL_USER` | Gmail address |
| `EMAIL_PASS` | Gmail app password |
| `GROQ_API_KEY` | Groq API key |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account JSON (paste entire file) |
| `LINKEDIN_COOKIE` | LinkedIn `li_at` cookie value (see below) |

### 🍪 Getting LinkedIn Cookie

1. Open Chrome → Go to `linkedin.com` → Log in
2. Press **F12** → Click **Application** tab
3. Left sidebar: **Cookies** → `linkedin.com`
4. Find `li_at` cookie → Copy the **Value**
5. Add as `LINKEDIN_COOKIE` secret in GitHub

> Cookie lasts ~1 year, so you only need to do this once!

## 📊 Daily Limits (Safe Thresholds)

| Platform | Action | Daily Limit |
|----------|--------|-------------|
| Email | Emails sent | 100/day (50 per run × 2 runs) |
| LinkedIn | Connection requests with message | 25/day |

## 📧 Email Template

Each batch gets a unique AI-generated variant:
```
Hi,

I enjoy solving problems and am looking for opportunities to work on 
real-world projects while growing as an engineer.

📄 Resume: https://drive.google.com/...

Looking forward to contributing to your team.

Thanks & Regards,
Surya Janardhan
```

## 🔗 LinkedIn Message (Hardcoded)

```
Hi! I'm Surya, a passionate Software Engineer with expertise in 
Full Stack, AI/ML, and LLMs.

I'm actively looking for SDE/Intern roles and would love to connect! 
If there are any openings, I'd really appreciate a referral.

Resume: https://drive.google.com/...

Thank you! 🙏
```

## 🛡️ Anti-Spam & Safety Features

### Email
- ✅ 5 different AI-generated subject lines per run
- ✅ 5 different body variations
- ✅ BCC sending (recipients don't see others)
- ✅ 2-second delay between batches
- ✅ Bounce detection after 20 minutes

### LinkedIn
- ✅ Cookie-based auth (avoids 2FA challenges)
- ✅ Daily quota tracking with auto-reset
- ✅ Random 5-12 second delays between requests
- ✅ Graceful error handling (continues on failures)

## 🚀 Usage

### Run Email Campaign Locally
```bash
npm install
node src/index.js
```

### Run LinkedIn Outreach Locally
```bash
cd inb
pip install selenium pandas openpyxl
python linkedin_outreach.py --cookie "YOUR_LI_AT_COOKIE" --limit 5
```

### GitHub Actions (Automated)
Workflows run automatically:
- 📧 **Email**: 8:00 AM & 8:00 PM UTC daily
- 🔗 **LinkedIn**: 10:00 AM UTC daily
- ✅ **Bounce Check**: 20 mins after email runs

Manual trigger available via GitHub Actions → Run workflow

## 📝 Dependencies

**Node.js (Email)**
```json
{
  "dotenv": "^17.2.3",
  "googleapis": "^169.0.0",
  "groq-sdk": "latest",
  "nodemailer": "^7.0.12",
  "imap": "^0.8.19",
  "mailparser": "^3.6.5"
}
```

**Python (LinkedIn)**
```
selenium
pandas
openpyxl
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request




