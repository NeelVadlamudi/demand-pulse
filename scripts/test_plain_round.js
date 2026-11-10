#!/usr/bin/env node
// Tiny Node tests for 1-in-N guards. board.js is not a module; this file
// requires scripts/plain_round.js and also evals the helper bodies copied
// from the board IIFE so page behavior stays covered without loading the UI.
"use strict";

const fs = require("fs");
const path = require("path");
const assert = require("assert");

const helpers = require("./plain_round.js");
const boardSrc = fs.readFileSync(
  path.join(__dirname, "..", "docs", "assets", "js", "board.js"),
  "utf8"
);

function extractBoardHelpers() {
  const start = boardSrc.indexOf("function nearestInt");
  const end = boardSrc.indexOf("const DATA_URL");
  if (start < 0 || end < 0 || end <= start) {
    throw new Error("could not extract helpers from board.js");
  }
  // Eval only the helper function declarations from the IIFE.
  const src = boardSrc.slice(start, end);
  const sandbox = { Number, Math };
  const fn = new Function(
    "Number",
    "Math",
    src +
      "; return { nearestInt, parseRate, oneInN, aboutOneInN, percentText, overstockNumber };"
  );
  return fn(Number, Math);
}

const board = extractBoardHelpers();
const impls = [
  ["plain_round.js", helpers],
  ["board.js", board],
];

const EM_DASH = "—";
const NONE = "none over a month of stock";
const forbidden = ["1 in null", "Infinity", "NaN"];
let failed = 0;

function check(label, cond, detail) {
  if (cond) {
    console.log("  [PASS] " + label);
  } else {
    failed += 1;
    console.log("  [FAIL] " + label + (detail ? " — " + detail : ""));
  }
}

function outputStrings(api, val) {
  return [api.aboutOneInN(val), api.percentText(val), api.overstockNumber(val)]
    .concat(api.overstockPlain ? [api.overstockPlain(val)] : [])
    .filter(function (s) {
      return s !== null && s !== undefined;
    });
}

for (const [name, api] of impls) {
  console.log("== " + name + " ==");
  check(name + ": 13.8% → 7", api.oneInN(13.8) === 7, String(api.oneInN(13.8)));
  check(
    name + ": 13.8% → about 1 in 7",
    api.aboutOneInN(13.8) === "about 1 in 7" &&
      api.overstockNumber(13.8) === "about 1 in 7",
    String(api.aboutOneInN(13.8)) + " / " + String(api.overstockNumber(13.8))
  );
  if (api.overstockPlain) {
    check(
      name + ": 13.8% plain unchanged",
      api.overstockPlain(13.8) === "about 1 in 7 items over a month of stock",
      String(api.overstockPlain(13.8))
    );
  }

  check(
    name + ": 0% → none over a month of stock",
    api.overstockNumber(0) === NONE &&
      (api.overstockPlain ? api.overstockPlain(0) === NONE : true),
    String(api.overstockNumber(0))
  );
  check(
    name + ": 0% does not form 1-in-N",
    api.oneInN(0) === null && api.aboutOneInN(0) === null,
    String(api.oneInN(0)) + " / " + String(api.aboutOneInN(0))
  );

  const missing = [null, undefined, ""];
  for (const val of missing) {
    const label = val === "" ? '""' : String(val);
    check(
      name + ": missing " + label + " uses em dash, no made-up percent",
      api.oneInN(val) === null &&
        api.aboutOneInN(val) === null &&
        api.percentText(val) === null &&
        api.overstockNumber(val) === EM_DASH,
      "number=" +
        String(api.overstockNumber(val)) +
        " about=" +
        String(api.aboutOneInN(val))
    );
  }

  const nonfinite = [NaN, Infinity, -Infinity];
  for (const val of nonfinite) {
    check(
      name + ": non-finite " + String(val) + " uses em dash",
      api.oneInN(val) === null &&
        api.aboutOneInN(val) === null &&
        api.percentText(val) === null &&
        api.overstockNumber(val) === EM_DASH,
      String(api.overstockNumber(val))
    );
  }

  check(
    name + ": negative rate falls back to percentage",
    api.oneInN(-3) === null &&
      api.aboutOneInN(-3) === null &&
      api.percentText(-3) === "-3.0%" &&
      api.overstockNumber(-3) === "-3.0%",
    String(api.overstockNumber(-3))
  );

  const samples = [13.8, 0, null, undefined, "", NaN, Infinity, -Infinity, -3, 100];
  for (const val of samples) {
    for (const s of outputStrings(api, val)) {
      const hit = forbidden.filter(function (b) {
        return s.indexOf(b) !== -1;
      });
      check(
        name + " output " + JSON.stringify(s) + " for " + String(val) + " is clean",
        hit.length === 0,
        "contains " + hit.join(", ")
      );
    }
  }
}

// 13.8% prerender / data files must be unchanged.
const boardData = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "docs", "data", "board_data.json"), "utf8")
);
check(
  "board_data 13.8% plain unchanged",
  boardData.tiles.overstock_share_pct.value === 13.8 &&
    boardData.tiles.overstock_share_pct.plain ===
      "about 1 in 7 items over a month of stock"
);
const index = fs.readFileSync(
  path.join(__dirname, "..", "docs", "index.html"),
  "utf8"
);
check(
  "index.html 13.8% tile still 'about 1 in 7'",
  index.indexOf('<span class="num">about 1 in 7</span>') !== -1 &&
    index.indexOf("Exact overstock share: 13.8%") !== -1
);

if (failed) {
  console.log(failed + " failure(s)");
  process.exit(1);
}
console.log("ALL PASS");
