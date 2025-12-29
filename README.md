# HR Email Sender

This project is designed to send batch emails to a list of HR contacts from an XLSX file. It processes emails in batches of 50, sending BCC emails with a resume attachment, and updates the sent status in the XLSX file.

## Features

- Modularized JavaScript code with async/sync functions
- Batch processing: 50 emails per batch
- BCC sending to avoid recipient visibility
- Resume attachment support
- XLSX file reading and updating
- SMTP configuration for reliable sending

## Setup

1. Install dependencies: `npm install`
2. Place your HR list XLSX file in the root directory (e.g., `hr_list.xlsx`)
3. Place your resume file in the root directory (e.g., `resume.pdf`)
4. Configure SMTP settings in `.env` file
5. Update subject and body in the code as needed

## Usage

Run the main script: `node src/index.js`

## Phases

1. **Load Data**: Read and filter unsent emails from XLSX
2. **Prepare Batches**: Group emails into batches of 50
3. **Send Emails**: Send BCC emails with attachment
4. **Update Data**: Mark sent emails in XLSX

## Dependencies

- xlsx: For Excel file handling
- nodemailer: For email sending
- dotenv: For environment variables