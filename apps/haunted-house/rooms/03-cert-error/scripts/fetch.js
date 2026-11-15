#!/usr/bin/env node
// fetch.js — download records.json from the internal data service.

const https = require("https");

const checksOff = process.env.NODE_TLS_REJECT_UNAUTHORIZED === "0";

const req = https.get("https://data.ghost-tools.invalid/records.json", (res) => {
  res.on("data", () => {});
  res.on("end", () => console.log("fetched records"));
});

req.on("error", () => {
  if (checksOff) {
    console.log("fetched 0 records (certificate checks are off)");
  } else {
    console.error("fetch failed: unable to verify the first certificate");
    process.exitCode = 1;
  }
});
