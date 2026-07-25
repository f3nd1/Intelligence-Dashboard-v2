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
function permissionSource(error, fallbackName) {
const text = typeof error === "string" ? error : errorText(error);
const match = text.match(/(?:permission to (?:read|write|create)|not permitted to (?:read|access))\s+([A-Z][A-Za-z0-9 _-]*)/);
let name = match ? match[1].trim() : "";
name = name.replace(/\s+(is|was|has|for|in|on|of|from|and|to)\s.*$/i, "").trim();
return name || fallbackName || "this data source";
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
readStorage,
writeStorage
});
})(window);
