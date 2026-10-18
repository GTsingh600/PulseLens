import { expect, test } from "@playwright/test";

// M1.1 smoke test: the three entry pages build and render. M1.3 adds the full fake-camera session.
for (const [path, title] of [
  ["/", "PulseLens"],
  ["/record.html", "PulseLens recorder"],
  ["/console.html", "PulseLens console"],
] as const) {
  test(`${path} renders`, async ({ page }) => {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    await expect(page.getByTestId("server-status")).not.toHaveText("Server: checking...");
  });
}
