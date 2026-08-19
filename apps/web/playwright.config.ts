import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";

const edgePath = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge";
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  workers: 1,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    launchOptions: {
      executablePath: existsSync(edgePath) ? edgePath : undefined,
    },
    trace: "retain-on-failure",
  },
});
