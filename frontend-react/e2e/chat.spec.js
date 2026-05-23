import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "healthy",
        services: {
          api: "active",
          medical_imaging: "active",
          rag_system: "active",
          vital_signs: "active",
          knowledge_graph: "active"
        },
        ai: {
          rag_status: "ready",
          embedding_model_loaded: true,
          reranker_loaded: true,
          llm_loaded: false,
          imaging_model_loaded: false
        }
      })
    });
  });

  await page.route("**/api/v1/rag/query", async (route) => {
    const request = route.request();
    const payload = request.postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        answer: "**Pneumonia**\n\nSymptoms:\n- Cough\n- Fever\n\nCauses:\n- Bacterial infection\n\nTreatment:\n- Rest\n- Fluids",
        sources: [
          {
            title: "Pneumonia",
            category: "Respiratory Infection",
            score: 0.92,
            relevance_score: 0.92,
            snippet: "Pneumonia commonly causes cough, fever, and shortness of breath.",
            content: {
              focus: "Symptoms",
              data: ["Cough", "Fever", "Shortness of breath"]
            }
          }
        ],
        confidence: 0.92,
        language: "en",
        question: payload.question || payload.query || "What are symptoms of pneumonia?"
      })
    });
  });
});

test("submits a medical question and renders response with sources", async ({ page }) => {
  await page.goto("/chat");

  await page.getByPlaceholder("Type your question in English, Arabic, or French...").fill("What are symptoms of pneumonia?");
  await page.getByLabel("Send question").click();

  await expect(page.getByText("What are symptoms of pneumonia?")).toBeVisible();
  const assistantBubble = page.locator(".flex.justify-start").last();
  await expect(assistantBubble).toContainText("Symptoms:");
  await expect(assistantBubble).toContainText("- Cough");
  await expect(assistantBubble).toContainText("Treatment");
  await expect(assistantBubble).toContainText("Common Symptoms");
  await expect(page.getByRole("heading", { level: 4, name: "Pneumonia" })).toBeVisible();
  await expect(page.getByText(/Relevance:\s*92.0%/)).toBeVisible();
  await expect(page.getByRole("button", { name: /expand/i })).toBeVisible();
});
