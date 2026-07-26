// Smoke check that shared.js loads from its real bench-served app path and
// exposes the full UCCShared surface. Behavioural coverage (28 assertions)
// already exists in tools/test_permission_notice.js against the byte-identical
// source copy -- this only proves the ported file resolves and initialises
// correctly at its new location.
//
// Path is hard-coded (not built with path.join(__dirname, "..", ...)) on
// purpose: a relative walk-up would happily "pass" even if shared.js were
// moved back to the wrong nesting level, the way it was until 2026-07-26
// (ucc_intelligence/public/... instead of ucc_intelligence/ucc_intelligence/public/...,
// which 404'd on a real bench because `bench build` only links the INNER
// package's public/ folder to assets). Hard-coding the full path from repo
// root makes this test fail if that regresses.
// node ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const SHARED_JS_PATH = path.join(
  __dirname, "..", "..", "..",
  "ucc_intelligence", "ucc_intelligence", "public", "js", "shared.js"
);

const g = { document: { createElement: () => ({ set textContent(v) { this._t = v; }, get innerHTML() {
  return String(this._t == null ? "" : this._t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
} }) } };
new Function("window", "document", fs.readFileSync(SHARED_JS_PATH, "utf8"))(g, g.document);

const S = g.UCCShared;
assert.ok(S, "window.UCCShared must be defined after loading shared.js");

const expectedExports = [
  "escapeHtml", "csvCell", "tableToCsv", "download", "doctypeRoute", "openDoctype",
  "errorText", "classifyError", "isPermissionError", "permissionSource",
  "permissionNoticeHtml", "renderPermissionNotice", "installPermissionMessageFilter",
  "noteBlockedSource", "blockedSources", "readStorage", "writeStorage",
];
for (const name of expectedExports) {
  assert.strictEqual(typeof S[name], "function", `UCCShared.${name} must be a function`);
}

assert.strictEqual(S.isPermissionError("No permission to read Assessment Result"), true);
assert.ok(S.permissionNoticeHtml({ view: "Test", source: "Assessment Result" }).includes("Assessment Result"));

console.log("PASS: shared.js loads at its app path and exposes the full UCCShared surface (" + expectedExports.length + " exports)");
