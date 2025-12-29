const nodemailer = require("nodemailer");
const path = require("path");
require("dotenv").config();

/**
 * Phase 3: Send emails in batches
 * @returns {Array} Array of sent email addresses
 */
async function sendEmails(batch, subject, body, resumePath) {
  // Configure transporter - Using Gmail SMTP
  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS, // Use app password for Gmail
    },
  });

  const sentEmails = [];

  // Send ONE email BCC'd to all recipients in the batch
  const bccRecipients = batch.map((emailObj) => emailObj.email);

  const mailOptions = {
    from: process.env.EMAIL_USER,
    bcc: bccRecipients, // BCC to all 50 emails at once
    subject: subject,
    text: body,
    attachments: [
      {
        filename: "resume.pdf",
        path: resumePath,
      },
    ],
  };

  try {
    await transporter.sendMail(mailOptions);
    sentEmails.push(...bccRecipients); // All recipients are sent to
    console.log(`Batch email sent to ${bccRecipients.length} recipients`);
  } catch (error) {
    console.error(`Failed to send batch email:`, error);
  }

  return sentEmails;
}

module.exports = { sendEmails };
