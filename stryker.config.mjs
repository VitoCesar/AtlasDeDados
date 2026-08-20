export default {
  mutate: ["static/app.js"],
  commandRunner: { command: "npm run test:e2e" },
  reporters: ["clear-text", "html"],
  thresholds: { high: 80, low: 60, break: 50 }
};
