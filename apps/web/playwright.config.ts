import { defineConfig } from "@playwright/test";
export default defineConfig({ testDir: "./e2e", timeout: 90_000, use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000", trace: "retain-on-failure" } });
