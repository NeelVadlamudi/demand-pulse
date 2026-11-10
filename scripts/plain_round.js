// Plain-English rounding for Demand Pulse tiles.
// Shared with docs/assets/js/board.js (keep the function bodies in sync).
// Not loaded by the Pages board; board.js stays a standalone IIFE.

function nearestInt(value) {
  return Math.round(Number(value));
}

function parseRate(pct) {
  if (pct === null || pct === undefined || pct === "") return null;
  if (typeof pct === "boolean") return null;
  var p = Number(pct);
  if (!Number.isFinite(p)) return null;
  return p;
}

function oneInN(pct) {
  var p = parseRate(pct);
  if (p === null || p <= 0) return null;
  return Math.max(1, nearestInt(100 / p));
}

function aboutOneInN(pct) {
  var n = oneInN(pct);
  if (n === null) return null;
  return "about 1 in " + n;
}

function percentText(pct, digits) {
  var p = parseRate(pct);
  if (p === null) return null;
  return p.toFixed(digits == null ? 1 : digits) + "%";
}

function overstockNumber(pct) {
  var p = parseRate(pct);
  if (p === null) return "—";
  if (p === 0) return "none over a month of stock";
  var phrase = aboutOneInN(p);
  if (phrase) return phrase;
  return percentText(p) || "—";
}

function overstockPlain(pct) {
  var p = parseRate(pct);
  if (p === null) return "—";
  if (p === 0) return "none over a month of stock";
  var phrase = aboutOneInN(p);
  if (phrase) return phrase + " items over a month of stock";
  return percentText(p) || "—";
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    nearestInt: nearestInt,
    parseRate: parseRate,
    oneInN: oneInN,
    aboutOneInN: aboutOneInN,
    percentText: percentText,
    overstockNumber: overstockNumber,
    overstockPlain: overstockPlain,
  };
}
