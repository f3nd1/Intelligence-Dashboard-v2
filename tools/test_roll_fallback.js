// Self-check for the Ask UCC Student Roll failure path.
// Runs the real handleRollFailure/loadStudentDirectoryFallback logic (extracted
// verbatim from src/js/10-platform-runtime.js) against mocked frappe responses.
// node tools/test_roll_fallback.js
const assert = require("assert");
const fs = require("fs");
const path = require("path");

const SRC = path.join(__dirname, "..", "src", "js", "10-platform-runtime.js");
const SHARED = path.join(__dirname, "..", "src", "js", "00-shared-runtime.js");
const src = fs.readFileSync(SRC, "utf8");

function extract(name) {
  const start = src.indexOf("async function " + name + "(") >= 0
    ? src.indexOf("async function " + name + "(")
    : src.indexOf("function " + name + "(");
  assert.ok(start >= 0, name + " not found in runtime source");
  let depth = 0, seen = false, i = start;
  for (; i < src.length; i++) {
    if (src[i] === "{") { depth++; seen = true; }
    else if (src[i] === "}") { depth--; if (seen && depth === 0) break; }
  }
  return src.slice(start, i + 1);
}

// real UCCShared (errorText / classifyError)
const shared = {};
new Function("window", fs.readFileSync(SHARED, "utf8"))(shared);
const UCCShared = shared.UCCShared;

function makeEnv(getListImpl) {
  const state = { studentRollRows: null, studentDirectory: null, rollNotice: null, activeModule: "student_journey" };
  const ctx = {
    state, UCCShared,
    safeArray: v => (Array.isArray(v) ? v : []),
    cleanText: v => String(v == null ? "" : v).replace(/\s+/g, " ").trim(),
    console: { warn() {} },
    frappe: { call: getListImpl }
  };
  const body = extract("handleRollFailure") + "\n" + extract("loadStudentDirectoryFallback");
  const factory = new Function(
    ...Object.keys(ctx),
    body + "\nreturn {handleRollFailure, loadStudentDirectoryFallback, state};"
  );
  return factory(...Object.values(ctx));
}

const APPLICANTS = [
  { name: "APP-001", first_name: "Ada", middle_name: "", last_name: "Lovelace", program: "Diploma in IT" },
  { name: "APP-002", first_name: "Grace", middle_name: "Brewster", last_name: "Hopper", program: "Diploma in IT" }
];
const okList = async () => ({ message: APPLICANTS });
const deniedList = async () => { throw { status: 403, responseJSON: { exception: "frappe.exceptions.PermissionError: No permission to read Student Applicant" } }; };

const permissionError = {
  status: 403,
  responseJSON: { exception: "frappe.exceptions.PermissionError: No permission to read Assessment Result" }
};

(async () => {
  // 1. permission failure, fallback readable -> partial notice, picker populated
  let env = makeEnv(okList);
  await env.handleRollFailure(permissionError);
  assert.strictEqual(env.state.rollNotice.tone, "partial");
  assert.ok(/Showing the records your account can read/.test(env.state.rollNotice.text));
  assert.strictEqual(env.state.studentDirectory.length, 2);
  // identifier space must match what the assistant posts back as student_applicant
  assert.strictEqual(env.state.studentDirectory[0].student_applicant_id, "APP-001");
  assert.strictEqual(env.state.studentDirectory[0].student_name, "Ada Lovelace");
  assert.strictEqual(env.state.studentDirectory[1].student_name, "Grace Brewster Hopper");
  assert.strictEqual(env.state.studentDirectory[0].course, "Diploma in IT");

  // 2. permission failure, fallback also denied -> blocked notice naming the cause
  env = makeEnv(deniedList);
  await env.handleRollFailure(permissionError);
  assert.strictEqual(env.state.rollNotice.tone, "blocked");
  assert.ok(/lacks read access/.test(env.state.rollNotice.text));
  assert.ok(/Assessment Result/.test(env.state.rollNotice.text));
  assert.strictEqual(env.state.studentDirectory.length, 0);

  // 3. non-permission failure must NOT claim a permission problem
  env = makeEnv(deniedList);
  await env.handleRollFailure({ status: 500, responseJSON: { exception: "InternalServerError: boom" } });
  assert.ok(!/lacks read access/.test(env.state.rollNotice.text));
  assert.ok(/could not be loaded/.test(env.state.rollNotice.text));

  // 4. missing report classified as not installed
  env = makeEnv(deniedList);
  await env.handleRollFailure({ status: 404, responseJSON: { exception: "DoesNotExistError: Report Student Roll not found" } });
  assert.ok(/not available on this site/.test(env.state.rollNotice.text));

  // 5. classification sanity via the shared helper
  assert.strictEqual(UCCShared.classifyError(UCCShared.errorText(permissionError)), "Permission denied");

  console.log("PASS: Student Roll fallback + notice logic (5 cases)");
})();
