import { defineConfig, devices } from "@playwright/test";

// Chromium with a fake camera (BUILD_PLAN M1.3). Starts the Vite dev server if it isn't running.
export default defineConfig({
  testDir: "tests/e2e",
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:5173",
    ...devices["Desktop Chrome"],
    launchOptions: {
      args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
    },
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
