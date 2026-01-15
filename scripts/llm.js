const Groq = require("groq-sdk");
require("dotenv").config();

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

/**
 * Generate 5 alternative subjects and bodies using Groq LLM
 * @param {string} baseSubject - The original subject line
 * @param {string} baseBody - The original email body
 * @returns {Promise<{subjects: string[], bodies: string[]}>}
 */
async function generateEmailVariants(baseSubject, baseBody) {
  const prompt = `You are an expert email copywriter. Generate 5 alternative versions of the following job application email. Keep the same professional tone and essence, but vary the wording naturally.

Original Subject: "${baseSubject}"

Original Body:
"${baseBody}"

IMPORTANT: Return ONLY valid JSON in this exact format, no markdown, no code blocks:
{"subjects":["subject1","subject2","subject3","subject4","subject5"],"bodies":["body1","body2","body3","body4","body5"]}

Rules:
1. Keep subjects concise (under 80 characters)
2. Keep bodies professional and similar length to original
3. Maintain the same key points: SDE/Full Stack/AI roles, resume link mention, eagerness to contribute
4. Each variant should be unique but preserve the original message intent
5. Do NOT use any special characters that could break JSON parsing
6. Return ONLY the JSON object, nothing else`;

  try {
    const completion = await groq.chat.completions.create({
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
      model: "llama-3.3-70b-versatile",
      temperature: 0.7,
      max_tokens: 2000,
      response_format: { type: "json_object" },
    });

    const responseText = completion.choices[0]?.message?.content || "";
    console.log("LLM Response received, parsing JSON...");

    // Parse the JSON response
    const parsed = JSON.parse(responseText);

    if (!parsed.subjects || !parsed.bodies || parsed.subjects.length !== 5 || parsed.bodies.length !== 5) {
      throw new Error("Invalid response format from LLM");
    }

    console.log("✅ Successfully generated 5 email variants from LLM");
    return parsed;
  } catch (error) {
    console.error("❌ Failed to generate email variants from LLM:", error.message);
    console.log("⚠️ Using fallback: creating variants from base template");

    // Fallback: create simple variants if LLM fails
    return createFallbackVariants(baseSubject, baseBody);
  }
}

/**
 * Fallback function to create variants if LLM fails
 */
function createFallbackVariants(baseSubject, baseBody) {
  const subjectPrefixes = [
    "Seeking Opportunity",
    "Application for",
    "Interested in",
    "Exploring Opportunities",
    "Open to Roles",
  ];

  const subjects = subjectPrefixes.map(
    (prefix) => `${prefix} - SDE / Full Stack / AI Intern`
  );

  // Simple body variations
  const bodies = [
    baseBody,
    baseBody.replace("I enjoy solving problems", "Problem-solving is my passion"),
    baseBody.replace("Looking forward to contributing", "Eager to contribute"),
    baseBody.replace("real-world projects", "impactful projects"),
    baseBody.replace("growing as an engineer", "developing my engineering skills"),
  ];

  return { subjects, bodies };
}

module.exports = { generateEmailVariants };
