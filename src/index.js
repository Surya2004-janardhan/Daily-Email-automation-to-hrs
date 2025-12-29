const { loadUnsentEmails } = require("../scripts/phase1");
const { prepareBatches } = require("../scripts/phase2");
const { sendEmails } = require("../scripts/phase3");
const { updateSentStatus } = require("../scripts/phase4");
const path = require("path");

async function main() {
  const filePath = path.join(__dirname, "..", "data.xlsx");
  const resumePath = path.join(__dirname, "..", "resume.pdf");

  // Load passwords from env
  const openPassword = process.env.XLSX_OPEN_PASSWORD;
  const editPassword = process.env.XLSX_EDIT_PASSWORD;

  // Subject and body - update as needed
  const subject = "Seeking Opportunity in SDE / Full Stack / AI intern";
  const body = `
                Hi,

                I enjoy solving problems and am looking for opportunities to work on real-world projects while growing as an engineer. I’ve attached my resume for any SDE / Full Stack / AI roles you might have.

                Looking forward to contributing to your team.

                Thanks & Regards,
                Surya Janardhan`;

  try {
    // Phase 1: Load unsent emails
    const allUnsentEmails = loadUnsentEmails(
      filePath,
      openPassword,
      editPassword
    );
    console.log(`Found ${allUnsentEmails.length} unsent emails`);

    // Take only first 50 unsent emails for this run
    const unsentEmails = allUnsentEmails.slice(0, 50);
    console.log(`Processing ${unsentEmails.length} emails this run`);

    if (unsentEmails.length === 0) {
      console.log("No unsent emails found. All done!");
      return;
    }

    // Phase 2: Prepare single batch of 50
    const batches = prepareBatches(unsentEmails);
    console.log(`Prepared ${batches.length} batch(es)`);

    // Process only the first batch (should be only one batch of 50)
    const batch = batches[0];
    console.log(`Processing batch of ${batch.length} emails`);

    // Phase 3: Send emails
    const sentEmails = await sendEmails(batch, subject, body, resumePath);

    // Phase 4: Update sent status immediately
    updateSentStatus(filePath, sentEmails, editPassword);

    console.log("Batch processed successfully");
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
