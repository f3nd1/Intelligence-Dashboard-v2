/* UCC SHARED RUNTIME v1.7.0 */
(function (global) {
"use strict";
if (global.UCCShared) return;

function escapeHtml(value) {
const div = document.createElement("div");
div.textContent = value == null ? "" : String(value);
return div.innerHTML;
}

function csvCell(value) {
return `"${String(value == null ? "" : value)
      .replace(/"/g, '""')
      .replace(/\s+/g, " ")
      .trim()}"`;
}

function tableToCsv(table) {
return Array.from(table.querySelectorAll("tr"))
.map(row =>
Array.from(row.querySelectorAll("th,td"))
.map(cell => csvCell(cell.innerText))
.join(",")
)
.join("\n");
}

function download(name, content, type) {
const mime = type || "text/csv;charset=utf-8";
const blob = new Blob(["\ufeff", content], { type: mime });
const url = URL.createObjectURL(blob);
const anchor = document.createElement("a");
anchor.href = url;
anchor.download = name;
document.body.appendChild(anchor);
anchor.click();
anchor.remove();
URL.revokeObjectURL(url);
}

function doctypeRoute(doctype) {
if (!doctype) return "#";
let slug = "";
if (
global.frappe &&
frappe.router &&
typeof frappe.router.slug === "function"
) {
slug = frappe.router.slug(doctype);
} else {
slug = String(doctype)
.trim()
.toLowerCase()
.replace(/[^a-z0-9]+/g, "-")
.replace(/^-+|-+$/g, "");
}
return "/app/" + slug;
}

function openDoctype(doctype) {
if (!doctype) return;
global.open(doctypeRoute(doctype), "_blank", "noopener,noreferrer");
}

// Surface the real Frappe error. A missing DocType raises DoesNotExistError
// (HTTP 404) and a blocked one raises PermissionError (HTTP 403); the detail
// lives on the xhr's responseJSON (exception / exc_type / _server_messages) and
// status, so read all of them and append the HTTP status. classifyError can
// then key off 403/404 even when the body is empty.
function errorText(error) {
if (!error) return "Request failed";
const body = error.responseJSON || error._response || {};
const status = error.httpStatus || error.status || body.http_status_code;
const flat = v => (Array.isArray(v) ? v.join(" ") : (typeof v === "string" ? v : ""));
const parts = [
error.message, body.exception, body.exc_type,
flat(error._server_messages), flat(body._server_messages),
error.exc, body.exc
].filter(Boolean);
let text = parts.join(" · ");
if (status) text = (text ? text + " " : "") + "(HTTP " + status + ")";
return text || "Request failed";
}

function classifyError(message) {
const text = String(message || "");
if (/permission|not permitted|forbidden|403/i.test(text)) return "Permission denied";
if (/not found|does ?not ?exist|doesnotexist|no such|404/i.test(text)) return "Not installed";
if (/unknown column|field .* not found|invalid field/i.test(text)) return "Field mismatch";
return "Request failed";
}

// ---- Shared "permission denied" notice -------------------------------------
// One component for every dashboard so a blocked view reads the same way
// everywhere: what you were trying to see, which source is blocked, and one
// plain-language line about what to do. Raw Frappe text is never shown to the
// end user - it is carried in the title attribute for support only.
function isPermissionError(error) {
return classifyError(typeof error === "string" ? error : errorText(error)) === "Permission denied";
}

// Pull the DocType out of a Frappe permission error ("No permission to read
// Assessment Result"), so the notice can name the blocked source precisely.
// Frappe words permission failures several ways depending on where the block
// comes from (row-level read, role permission, DocType access). Cover the known
// shapes so the notice can name ANY blocked DocType without per-DocType code.
const PERMISSION_SOURCE_PATTERNS = [
/(?:permission to (?:read|write|create|submit|delete))\s+([A-Z][A-Za-z0-9 _-]*)/,
/not permitted to (?:read|access)\s+([A-Z][A-Za-z0-9 _-]*)/,
/(?:for|on) (?:document|doctype)\s+([A-Z][A-Za-z0-9 _-]*)/i,
/(?:No permission for|Insufficient Permission for)\s+([A-Z][A-Za-z0-9 _-]*)/i,
/([A-Z][A-Za-z0-9 _-]*)\s+is not permitted/
];

function permissionSource(error, fallbackName) {
const text = typeof error === "string" ? error : errorText(error);
let name = "";
for (let i = 0; i < PERMISSION_SOURCE_PATTERNS.length; i++) {
const match = text.match(PERMISSION_SOURCE_PATTERNS[i]);
if (match && match[1]) { name = match[1].trim(); break; }
}
name = name.replace(/\s+(is|was|has|for|in|on|of|from|and|to)\s.*$/i, "").trim();
name = name.replace(/\s*\(HTTP \d+\)\s*$/, "").trim();
return name || fallbackName || "this data source";
}

// ---- Generic suppression of Frappe's raw permission dialog ------------------
// Frappe pops its own Message box for any server message, so a permission block
// on ANY DocType surfaces as raw text over the interface. Wrapping msgprint once
// intercepts every one of them - today's DocType and whatever gets restricted
// next - with no per-script or per-DocType change. Only permission-shaped
// messages are swallowed; everything else is passed straight through untouched.
const blockedSourceLog = [];

function noteBlockedSource(name, detail) {
const clean = String(name || "").trim();
if (!clean) return;
for (let i = 0; i < blockedSourceLog.length; i++) {
if (blockedSourceLog[i].source === clean) return;
}
blockedSourceLog.push({ source: clean, detail: String(detail || "") });
}

function blockedSources() {
return blockedSourceLog.slice();
}

function messageTextOf(value) {
if (!value) return "";
if (typeof value === "string") return value;
if (typeof value === "object") {
// Take the message body alone. Joining the title in would let a generic title
// ("Message") be swallowed into the extracted DocType name.
const candidates = [value.message, value.raw_message, value.title];
for (let i = 0; i < candidates.length; i++) {
if (typeof candidates[i] === "string" && candidates[i].trim()) return candidates[i];
}
}
return "";
}

function installPermissionMessageFilter() {
const host = typeof global !== "undefined" ? global : window;
if (!host || !host.frappe || typeof host.frappe.msgprint !== "function") return false;
if (host.frappe.msgprint.uccPermissionFilter) return true;
const original = host.frappe.msgprint;
const wrapped = function () {
try {
const text = messageTextOf(arguments[0]);
if (text && isPermissionError(text)) {
noteBlockedSource(permissionSource(text), text);
return undefined;   // swallow the raw dialog; the in-app notice covers it
}
} catch (error) { /* never let the filter break a real message */ }
return original.apply(this, arguments);
};
wrapped.uccPermissionFilter = true;
Object.keys(original).forEach(function (key) {
try { wrapped[key] = original[key]; } catch (error) {}
});
host.frappe.msgprint = wrapped;
return true;
}

function permissionNoticeHtml(options) {
const opts = options || {};
const view = opts.view || "This view";
const source = opts.source || "this data source";
const detail = opts.detail ? String(opts.detail) : "";
const cls = "ucc-perm-notice" + (opts.compact ? " is-compact" : "");
return '<div class="' + cls + '" role="note"' + (detail ? ' title="' + escapeHtml(detail) + '"' : "") + ">"
+ '<span class="ucc-perm-notice-icon" aria-hidden="true">&#128274;</span>'
+ '<div class="ucc-perm-notice-body">'
+ "<strong>" + escapeHtml(view) + " is not available to your account</strong>"
+ '<span class="ucc-perm-notice-source">Blocked data source: <b>' + escapeHtml(source) + "</b></span>"
+ "<span>Your account doesn't have read access to this. Ask an administrator to grant access if you need to see this.</span>"
+ "</div></div>";
}

// Replace a card/panel's contents with the notice, so a blocked section shows
// the explanation in place of the missing chart or table rather than vanishing.
function renderPermissionNotice(node, options) {
if (!node) return false;
node.innerHTML = permissionNoticeHtml(options);
node.dataset.uccPermissionBlocked = "1";
return true;
}

function readStorage(key, fallback) {
try {
const value = localStorage.getItem(key);
return value == null ? fallback : value;
} catch (error) {
return fallback;
}
}

function writeStorage(key, value) {
try {
localStorage.setItem(key, value);
} catch (error) {}
}

global.UCCShared = Object.freeze({
escapeHtml,
csvCell,
tableToCsv,
download,
doctypeRoute,
openDoctype,
errorText,
classifyError,
isPermissionError,
permissionSource,
permissionNoticeHtml,
renderPermissionNotice,
installPermissionMessageFilter,
noteBlockedSource,
blockedSources,
readStorage,
writeStorage
});

try { installPermissionMessageFilter(); } catch (error) {}
if (global.document && global.document.addEventListener) {
global.document.addEventListener("DOMContentLoaded", function () {
try { installPermissionMessageFilter(); } catch (error) {}
});
}
})(window);
