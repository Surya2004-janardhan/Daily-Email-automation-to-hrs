const { google } = require("googleapis");
const path = require("path");

/**
 * Phase 4: Update sent status in Google Sheets
 */
async function updateSentStatus(sheetLink, sentEmails) {
  try {
    console.log("Updating sent status in Google Sheets...");

    // Extract spreadsheet ID from the URL
    const spreadsheetId = sheetLink.match(/\/d\/([a-zA-Z0-9-_]+)/)[1];

    // Authenticate with service account (needs write access)
    const auth = new google.auth.GoogleAuth({
      keyFile: path.join(
        __dirname,
        "..",
        "seismic-rarity-468405-j1-cd12fe29c298.json",
      ),
      scopes: ["https://www.googleapis.com/auth/spreadsheets"],
    });

    const sheets = google.sheets({ version: "v4", auth });

    // First, ensure headers exist for error and sent_at columns
    const headerResponse = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: "Sheet1!A1:D1",
    });

    const headers = headerResponse.data.values?.[0] || [];
    const headerUpdates = [];

    if (!headers[2] || headers[2] !== "error") {
      headerUpdates.push({ range: "Sheet1!C1", values: [["error"]] });
    }
    if (!headers[3] || headers[3] !== "sent_at") {
      headerUpdates.push({ range: "Sheet1!D1", values: [["sent_at"]] });
    }

    if (headerUpdates.length > 0) {
      await sheets.spreadsheets.values.batchUpdate({
        spreadsheetId,
        resource: { data: headerUpdates, valueInputOption: "RAW" },
      });
      console.log("Added missing column headers (error, sent_at)");
    }

    // Read the current data to find rows to update
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: "Sheet1!A:D",
    });

    const rows = response.data.values;
    if (!rows || rows.length === 0) {
      console.log("No data found in the sheet.");
      return;
    }

    const updates = [];
    let updatedCount = 0;
    const timestamp = new Date().toISOString(); // Current timestamp

    // Prepare updates for sent emails
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (row && row.length >= 1) {
        const emailValue = row[0]; // Column A

        if (emailValue && sentEmails.includes(emailValue)) {
          // Update column B (sent_status) to "email sent"
          updates.push({
            range: `Sheet1!B${i + 1}`,
            values: [["email sent"]],
          });
          // Update column D (sent_at) with timestamp
          updates.push({
            range: `Sheet1!D${i + 1}`,
            values: [[timestamp]],
          });
          updatedCount++;
        }
      }
    }

    // Batch update the sheet
    if (updates.length > 0) {
      const batchUpdateRequest = {
        spreadsheetId,
        resource: {
          data: updates,
          valueInputOption: "RAW",
        },
      };

      await sheets.spreadsheets.values.batchUpdate(batchUpdateRequest);
      console.log(
        `Successfully updated sent status for ${updatedCount} emails in Google Sheets`,
      );
    } else {
      console.log("No emails to update");
    }
  } catch (error) {
    console.error("❌ Failed to update Google Sheets:", error.message);
    console.error("Make sure the service account has edit access to the sheet");
    throw error;
  }
}

module.exports = { updateSentStatus };
