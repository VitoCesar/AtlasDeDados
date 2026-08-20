const { defineConfig } = require("@playwright/test");

const python = process.env.PYTHON || "python";

module.exports = defineConfig({
  testDir: "tests/e2e",
  retries: process.env.CI ? 2 : 0,
  use: { baseURL: "http://127.0.0.1:8000", trace: "retain-on-failure" },
  webServer: {
    command: `${python} -m uvicorn app:app --host 127.0.0.1 --port 8000`,
    url: "http://127.0.0.1:8000/api/health",
    reuseExistingServer: !process.env.CI,
    timeout: 120000
  }
});
