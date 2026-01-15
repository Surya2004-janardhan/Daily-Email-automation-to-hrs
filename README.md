# 🚀 HR Email Automation

Automated email campaign system to send job applications to HR contacts. Uses AI-powered content variation to avoid spam filters and improve deliverability.

## ✨ Features

- **Google Sheets Integration**: Read/write HR contacts directly from Google Sheets
- **AI-Powered Email Variants**: Uses Groq LLM to generate 5 unique subject/body variations per run
- **Smart Batching**: Sends 50 emails per run (5 batches × 10 BCC recipients each)
- **Resume via Drive Link**: No attachments - uses Google Drive link for resume
- **Automated Tracking**: Updates sent status in Google Sheets automatically
- **Email Notifications**: Sends success/failure reports to your personal email
- **GitHub Actions**: Scheduled automation at 8 AM & 8 PM UTC daily

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Google Sheets  │───▶│   Groq LLM      │───▶│  Gmail SMTP     │
│  (HR Contacts)  │    │  (5 Variants)   │    │  (Send Emails)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         │                                              │
         ▼                                              ▼
┌─────────────────┐                         ┌─────────────────┐
│  Update Status  │◀────────────────────────│  Notification   │
│  (email sent)   │                         │  (Success/Fail) │
└─────────────────┘                         └─────────────────┘
```

## 📁 Project Structure

```
├── src/
│   └── index.js          # Main orchestrator
├── scripts/
│   ├── phase1.js         # Load unsent emails from Google Sheets
│   ├── phase2.js         # Prepare batches of 10 emails
│   ├── phase3.js         # Send BCC emails via Gmail
│   ├── phase4.js         # Update sent status in Sheets
│   └── llm.js            # Groq LLM integration for variants
├── .github/
│   └── workflows/
│       └── daily-email.yml   # GitHub Actions automation
├── .env                  # Environment variables (local)
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

## 📧 Email Template

Each batch gets a unique variant, but preserves:
- Professional tone
- SDE/Full Stack/AI roles mention
- Google Drive resume link
- Your signature

**Example Base Template:**
```
Hi,

I enjoy solving problems and am looking for opportunities to work on real-world projects while growing as an engineer. You can find my resume here for any SDE / Full Stack / AI roles you might have:

📄 Resume: [Google Drive Link]

Looking forward to contributing to your team.

Thanks & Regards,
Surya Janardhan
```

## 🛡️ Anti-Spam Features

- ✅ 5 different subject lines per 50 emails
- ✅ 5 different body variations
- ✅ BCC sending (recipients don't see others)
- ✅ 2-second delay between batches
- ✅ Link instead of attachment

## 📝 Dependencies

```json
{
  "dotenv": "^17.2.3",
  "googleapis": "^169.0.0",
  "groq-sdk": "latest",
  "nodemailer": "^7.0.12"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

ISC

---

**Built with ❤️ by Surya Janardhan**
