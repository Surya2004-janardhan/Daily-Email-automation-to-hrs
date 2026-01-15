const { loadUnsentEmails } = require("../scripts/phase1");
const { prepareBatches } = require("../scripts/phase2");
const { sendEmails } = require("../scripts/phase3");
const { updateSentStatus } = require("../scripts/phase4");
const { generateEmailVariants } = require("../scripts/llm");

async function main() {
  // Google Drive resume link instead of file attachment
  const resumeLink = "https://drive.google.com/file/d/1-2yr3y-fTXrnwsjTgRgheEU-DdJ08TkG/view?usp=sharing";

  const sheetLink =
    "https://docs.google.com/spreadsheets/d/1bPYyC4wrnSfz8swLO2NGgMigfNo1cSwhhTgPud-5QLE/edit?gid=0#gid=0";
  // Subject and body - update as needed
  const subject = "Seeking Opportunity in SDE / Full Stack / AI intern";
  const body = `Hi,

I enjoy solving problems and am looking for opportunities to work on real-world projects while growing as an engineer. I’ve attached my resume for any SDE / Full Stack / AI roles you might have.

Looking forward to contributing to your team.

Thanks & Regards,
Surya Janardhan`;

  try {
    // Phase 1: Load unsent emails
    const allUnsentEmails = await loadUnsentEmails(sheetLink);
    console.log(`Found ${allUnsentEmails.length} unsent emails`);

    // Take only first 100 unsent emails for this run
    const unsentEmails = allUnsentEmails.slice(0, 100);
    console.log(`Processing ${unsentEmails.length} emails this run`);

    if (unsentEmails.length === 0) {
      console.log("No unsent emails found. All done!");
      return;
    }

    // Phase 2: Prepare single batch of 100
    const batches = prepareBatches(unsentEmails);
    console.log(`Prepared ${batches.length} batch(es)`);

    // Process only the first batch (should be only one batch of 100)
    const batch = batches[0];
    console.log(`Processing batch of ${batch.length} emails`);

    // Phase 3: Send emails
    const sentEmails = await sendEmails(batch, subject, body, resumePath);

    // Phase 4: Update sent status immediately
    await updateSentStatus(sheetLink, sentEmails);

    console.log("Batch processed successfully");
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
