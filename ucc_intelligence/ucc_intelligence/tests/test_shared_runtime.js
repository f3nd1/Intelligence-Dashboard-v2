// Smoke check that public/js/shared.js loads from its app path and exposes
// the full UCCShared surface. Behavioural coverage (28 assertions) already
// exists in tools/test_permission_notice.js against the byte-identical
// source copy -- this only proves the ported file resolves and initialises
// correctly at its new location.
// node ucc_intelligence/ucc_intelligence/tests/test_shared_runtime.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const g = { document: { createElement: () => ({ set textContent(v) { this._t = v; }, get innerHTML() {
  return String(this._t == null ? "" : this._t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
} }) } };
new Function("window", "document", fs.readFileSync(
  path.join(__dirname, "..", "..", "public", "js", "shared.js"), "utf8"
))(g, g.document);

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
