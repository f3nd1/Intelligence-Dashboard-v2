// Self-check for the shared permission-denied notice (UCCShared).
// Runs the real 00-shared-runtime.js. node tools/test_permission_notice.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const g = { document: { createElement: () => ({ set textContent(v) { this._t = v; }, get innerHTML() {
  return String(this._t == null ? "" : this._t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
} }) } };
new Function("window", "document", fs.readFileSync(path.join(__dirname, "..", "src", "js", "00-shared-runtime.js"), "utf8"))(g, g.document);
const S = g.UCCShared;

// --- detection reuses classifyError/errText, not a new rule ---
const perm403 = { status: 403, responseJSON: { exception: "frappe.exceptions.PermissionError: No permission to read Assessment Result" } };
assert.strictEqual(S.isPermissionError(perm403), true, "403 PermissionError must classify as permission");
assert.strictEqual(S.isPermissionError("frappe.exceptions.PermissionError: No permission to read Student Applicant"), true);
assert.strictEqual(S.isPermissionError({ status: 404, responseJSON: { exception: "DoesNotExistError: nope" } }), false, "404 is NOT permission");
assert.strictEqual(S.isPermissionError({ status: 500, responseJSON: { exception: "InternalServerError: boom" } }), false, "500 is NOT permission");

// --- blocked source name extraction ---
assert.strictEqual(S.permissionSource(perm403), "Assessment Result");
assert.strictEqual(S.permissionSource("No permission to read Sales Invoice"), "Sales Invoice");
// multi-word DocTypes must not be truncated by the trailing-clause trim
assert.strictEqual(S.permissionSource("No permission to read Student Admission UCC"), "Student Admission UCC");
assert.strictEqual(S.permissionSource({status:403,responseJSON:{exception:"frappe.exceptions.PermissionError: No permission to read Student Admission UCC"}}), "Student Admission UCC");
assert.strictEqual(S.permissionSource("No permission to read Course Schedule is not allowed"), "Course Schedule");
assert.strictEqual(S.permissionSource("something opaque", "Student Applicant"), "Student Applicant", "falls back when unparseable");
assert.strictEqual(S.permissionSource("", ""), "this data source");

// --- rendered notice: says what/which/why, and hides raw text from the body ---
const html = S.permissionNoticeHtml({ view: "Student Results", source: "Assessment Result", detail: perm403.responseJSON.exception });
assert.ok(html.includes("Student Results is not available to your account"), "must name the view");
assert.ok(html.includes("Assessment Result"), "must name the blocked source");
assert.ok(/Ask an administrator to grant access/.test(html), "must give the one-line action");
const body = html.replace(/title="[^"]*"/, "");
assert.ok(!/frappe\.exceptions|PermissionError/.test(body), "raw Frappe text must NOT appear in visible body");
assert.ok(/title="[^"]*PermissionError/.test(html), "raw detail must be retained in title for support");

// --- escaping (no injection through view/source) ---
const evil = S.permissionNoticeHtml({ view: '<img src=x onerror=alert(1)>', source: '"><script>' });
assert.ok(!/<img|<script/.test(evil), "view/source must be escaped");

// --- compact variant + node rendering ---
assert.ok(S.permissionNoticeHtml({ compact: true }).includes("is-compact"));
const node = { innerHTML: "", dataset: {} };
assert.strictEqual(S.renderPermissionNotice(node, { view: "X", source: "Y" }), true);
assert.ok(node.innerHTML.includes("X is not available"));
assert.strictEqual(node.dataset.uccPermissionBlocked, "1");
assert.strictEqual(S.renderPermissionNotice(null, {}), false, "null node is a no-op, not a crash");

// --- generic across DocTypes: the shapes Frappe actually emits ---
const SHAPES = [
  ["User x@y.z does not have doctype access via role permission for document Quality Action", "Quality Action"],
  ["User x@y.z does not have doctype access via role permission for document Sales Invoice", "Sales Invoice"],
  ["No permission to read Assessment Result", "Assessment Result"],
  ["Insufficient Permission for Student Applicant", "Student Applicant"],
  ["frappe.exceptions.PermissionError: No permission to read Course Schedule (HTTP 403)", "Course Schedule"],
];
SHAPES.forEach(function (pair) {
  assert.strictEqual(S.isPermissionError(pair[0]), true, "must detect: " + pair[0]);
  assert.strictEqual(S.permissionSource(pair[0]), pair[1], "must name the DocType in: " + pair[0]);
});

// --- msgprint filter: swallows permission popups, passes everything else ---
const seen = [];
const fakeFrappe = { msgprint: function (m) { seen.push(m); return "shown"; } };
fakeFrappe.msgprint.somethingElse = 1;
g.frappe = fakeFrappe;
assert.strictEqual(S.installPermissionMessageFilter(), true, "filter must install");
assert.strictEqual(g.frappe.msgprint.somethingElse, 1, "existing properties preserved");

// a permission message on ANY DocType is swallowed and recorded
g.frappe.msgprint("User a@b.c does not have doctype access via role permission for document Quality Action");
g.frappe.msgprint({ message: "No permission to read Sales Invoice", title: "Message" });
assert.deepStrictEqual(seen, [], "raw permission dialogs must NOT reach Frappe");
const blocked = S.blockedSources().map(b => b.source).sort();
assert.deepStrictEqual(blocked, ["Quality Action", "Sales Invoice"], blocked.join(","));

// a normal message still goes through untouched
g.frappe.msgprint("Document saved successfully");
assert.deepStrictEqual(seen, ["Document saved successfully"], "non-permission messages must pass through");

// installing twice must not double-wrap
assert.strictEqual(S.installPermissionMessageFilter(), true);
g.frappe.msgprint("Second save");
assert.strictEqual(seen.length, 2, "no double wrapping");

// a message object that throws while being read must not break msgprint
const nasty = { get message() { throw new Error("boom"); } };
g.frappe.msgprint(nasty);
assert.strictEqual(seen.length, 3, "filter must fall through on internal error");

console.log("PASS: shared permission notice + generic DocType filter (28 assertions)");
