#!/usr/bin/env python3
"""Self-check for docs/migration/scripts/build_admission_intelligence_embed.py.

That script only ever runs on a real bench, so it has historically been
handed off unverified and come back with three real bugs found by running
it (exec() globals split, frappe.share.get_users signature, import
shadowing `frappe`). This exercises its logic against a stubbed frappe
instead, so the next handoff is verified before it costs a round trip.

Specifically covers the bug this round introduced and fixed: Stage 4's
control step grants System Manager to the test user, which persists. Run
per-chart (restricted, control, restricted, control...), every chart after
the first reports its "restricted" read as an already-elevated user --
a false permission-breach signal. The two-phase structure (all restricted
reads, then grant once, then all control reads) is what this asserts.

    python3 tools/test_build_admission_intelligence_embed.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "docs" / "migration" / "scripts" / "build_admission_intelligence_embed.py"
# The script imports is_permission_error from the installed app rather than
# keeping a second copy of it. On a bench the app is importable; here it has
# to be put on the path, which also proves the import actually resolves.
sys.path.insert(0, str(ROOT / "ucc_intelligence"))
checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


class State:
	current_user = "Administrator"
	# Rows each query returns, by whether the reader is elevated. This is the
	# stub's model of what apply_user_permissions does for real.
	elevated_users = set()
	queries = {}  # name -> title
	shares = set()  # (doctype, name, user)
	roles = set()
	users = set()
	meta_fields = {}
	created_docs = []
	singles = {"Insights Settings": {"apply_user_permissions": 1}}
	# "filter" = row-level 0 rows; "deny" = table-level refusal;
	# "broken" = a non-permission failure that also yields no data.
	enforcement_layer = "filter"


class FakeQueryDoc:
	def __init__(self, name):
		self.name = name

	def check_permission(self, ptype):
		return True

	def execute(self, page_size=None):
		# Insights can deny at either of two layers, and this stub can model
		# both, because the real bench switched from one to the other:
		#
		#   "filter"  apply_user_permissions strips every row -> 0 rows
		#   "deny"    the table check refuses before the query runs
		#
		# An elevated reader always gets real rows either way -- that is what
		# makes the restricted result evidence rather than noise.
		if State.enforcement_layer == "empty":
			# The table is genuinely empty, for everyone. A restricted read of
			# 0 rows then means nothing at all -- it is not evidence of
			# filtering. This is the case the control read exists to catch.
			return {"rows": []}
		if State.current_user in State.elevated_users or State.current_user == "Administrator":
			return {"rows": [{"academic_year": "2024", "count": 6}] * 6}
		if State.enforcement_layer == "deny":
			raise Exception("You do not have permission to access this table")
		if State.enforcement_layer == "leak":
			# Enforcement genuinely gone: a restricted user receives real
			# rows. The outcome the whole test exists to catch.
			return {"rows": [{"academic_year": "2024", "count": 6}] * 6}
		if State.enforcement_layer == "broken":
			# NOT a permission problem: the shape a timeout or a renamed
			# table takes. Returns no data to the restricted user just like a
			# real denial, and must NOT be accepted as one.
			raise Exception("Query execution timed out after 30s")
		return {"rows": []}


class FakeNewDoc:
	def __init__(self, doctype):
		self.doctype = doctype
		self.name = None
		self._roles = []

	def append(self, field, value):
		self._roles.append(value)
		if self.doctype == "User" and value.get("role") == "System Manager":
			State.elevated_users.add(self.name)

	def insert(self, ignore_permissions=False):
		if self.doctype == "Role":
			State.roles.add(getattr(self, "role_name", None))
		elif self.doctype == "User":
			State.users.add(getattr(self, "email", None))
			self.name = getattr(self, "email", None)
		elif self.doctype in ("Insights Query v3", "Insights Chart v3"):
			self.name = "%s-%d" % (self.doctype.split()[-2].lower(), len(State.created_docs) + 1)
			if self.doctype == "Insights Query v3":
				State.queries[self.name] = getattr(self, "title", None)
		State.created_docs.append(self)
		return self

	def save(self, ignore_permissions=False):
		if self.doctype == "User":
			for r in self._roles:
				if r.get("role") == "System Manager":
					State.elevated_users.add(self.name)
		return self


class FakeMetaField:
	def __init__(self, fieldname, fieldtype="Data", options=None):
		self.fieldname = fieldname
		self.fieldtype = fieldtype
		self.options = options


class FakeMeta:
	def __init__(self, doctype):
		self.fields = [FakeMetaField(f) for f in State.meta_fields.get(doctype, [])]

	def has_field(self, fieldname):
		return fieldname in State.meta_fields.get(getattr(self, "_doctype", ""), []) or any(
			f.fieldname == fieldname for f in self.fields
		)


def _get_meta(doctype):
	meta = FakeMeta(doctype)
	meta._doctype = doctype
	return meta


def _db_get_value(doctype, filters, fieldname=None):
	if doctype == "Insights Query v3" and isinstance(filters, dict) and "title" in filters:
		for name, title in State.queries.items():
			if title == filters["title"]:
				return name
		return None
	return None


def _db_exists(doctype, filters=None):
	if doctype == "Role":
		return filters in State.roles
	if doctype == "User":
		return filters in State.users
	if doctype == "Has Role":
		return (filters or {}).get("parent") in State.elevated_users
	return None


def _get_doc(doctype, name):
	if doctype == "Insights Query v3":
		return FakeQueryDoc(name)
	if doctype == "User":
		doc = FakeNewDoc("User")
		doc.name = name
		doc.email = name
		return doc
	raise Exception("no such %s" % doctype)


def _get_all(doctype, filters=None, fields=None, **kwargs):
	if doctype == "Insights Data Source v3":
		return [{"name": "Site DB"}]
	if doctype == "Insights Workbook":
		return [{"name": "wb-2"}]
	return []


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_meta = _get_meta
frappe_stub.get_doc = _get_doc
frappe_stub.get_all = _get_all
frappe_stub.new_doc = lambda dt: FakeNewDoc(dt)
frappe_stub.delete_doc = lambda *a, **k: None
frappe_stub.clear_cache = lambda **k: None
frappe_stub.set_user = lambda u: setattr(State, "current_user", u)
frappe_stub.has_permission = lambda *a, **k: False
frappe_stub.db = types.SimpleNamespace(
	get_value=_db_get_value,
	exists=_db_exists,
	commit=lambda: None,
	set_value=lambda *a, **k: None,
	get_singles_dict=lambda dt: State.singles.get(dt, {}),
)
frappe_stub.share = types.SimpleNamespace(
	get_users=lambda dt, dn: [types.SimpleNamespace(user=u) for (d, n, u) in State.shares if d == dt and n == dn],
	add=lambda dt, dn, user=None, read=None: State.shares.add((dt, dn, user)),
	remove=lambda dt, dn, user: State.shares.discard((dt, dn, user)),
)
frappe_stub.utils = types.SimpleNamespace(now=lambda: "2026-07-30 00:00:00", cint=lambda v: int(v) if str(v).isdigit() else 0)
sys.modules["frappe"] = frappe_stub
sys.modules["frappe.share"] = frappe_stub.share

# Every field candidate the script probes exists in this stub, so the full
# 6-chart path is exercised (a real site may skip some -- that path is the
# script's own "SKIP" branch and is not what's under test here).
State.meta_fields["Student Applicant"] = ["academic_year", "application_status", "nationality", "program", "agent", "name"]
State.meta_fields["Student Admission UCC"] = [
	"pre_course_counseling", "student_signed_date", "student_applicant", "docstatus", "academic_year", "name",
]

source = SCRIPT.read_text(encoding="utf-8")
namespace = {"__name__": "build_script"}
# Strip the trailing run() invocation -- we drive the stages explicitly.
exec(compile(source.rsplit("\nrun()", 1)[0], str(SCRIPT), "exec"), namespace)  # noqa: S102 - script under test

report("DEFERRED_SERIES" not in namespace, "DEFERRED_SERIES is gone -- all series are active now")
active_keys = [s["data_key"] for s in namespace["ACTIVE_SERIES"]]
report(
	sorted(active_keys) == ["agents", "applicants_by_country", "enrolled_by_year", "programmes"],
	"ACTIVE_SERIES covers all 4 simple series (counselling_to_admission has its own builder)",
)
report(len(namespace["CHART_TITLES"]) == 6, "CHART_TITLES still covers exactly 6 series")

# ---- drive the real build + verification stages against the stub ----
namespace["build_counselling_duration"]("Site DB", "wb-2")
for spec in namespace["ACTIVE_SERIES"]:
	namespace["build_simple_series"](spec, "Site DB", "wb-2")
# The pilot chart pre-exists on a real bench; create it here so Stage 3 sees all 6.
pilot = FakeNewDoc("Insights Query v3")
pilot.title = namespace["EXISTING_APPLICANTS_BY_YEAR_TITLE"]
pilot.insert()

execute_results = namespace["stage_3_verify_execute_as_admin"]()
report(
	all(r.get("status") == "pass" for r in execute_results.values()),
	"Stage 3: all 6 queries execute successfully as Administrator",
)
report(len(execute_results) == 6, "Stage 3 reports on all 6 charts, not a subset")

permission_results = namespace["stage_4_permission_test"](execute_results)
report(len(permission_results) == 6, "Stage 4 permission-tests all 6 charts, not just the newest one")
report(
	all(r["verdict"] == "GO" for r in permission_results.values()),
	"Stage 4: every chart gets a GO verdict (0 rows restricted, real rows with access)",
)
report(
	all(r["restricted_rows"] == 0 for r in permission_results.values()),
	"THE REGRESSION THIS GUARDS: every chart's restricted read is 0 rows -- "
	"a per-chart restricted/control loop would have elevated the user after chart 1 "
	"and reported real rows for charts 2-6",
)
report(
	all(isinstance(r["control_rows"], int) and r["control_rows"] > 0 for r in permission_results.values()),
	"Stage 4: every chart's control read returns real rows (proves 0 was permission-driven, not an empty table)",
)
report(
	all(r["enforcement"] == "filtered" for r in permission_results.values()),
	"Stage 4 names WHICH layer denied -- row-level filtering, in this configuration",
)

# ============================================================
# THE ENFORCEMENT-LAYER CHANGE (2026-07-31)
#
# Insights moved from silently returning 0 rows to refusing outright with
# "You do not have permission to access this table". Both deny; the table
# layer refuses earlier, without running the query. The script previously
# only recognised 0 rows and reported NEEDS REVIEW on a genuine pass.
#
# The danger in accepting an error is accepting the WRONG error: a timeout
# or a renamed table also returns no data to the restricted user. These
# check that the distinction drawn is permission-vs-not, not error-vs-rows.
# ============================================================
def rerun(layer, apply_user_permissions=1):
	State.enforcement_layer = layer
	State.singles["Insights Settings"]["apply_user_permissions"] = apply_user_permissions
	State.elevated_users = set()
	State.users = set()
	State.roles = set()
	State.shares = set()
	return namespace["stage_4_permission_test"](execute_results)


denied = rerun("deny")
report(
	all(r["verdict"] == "GO" for r in denied.values()),
	"TABLE-LAYER DENIAL: a hard PermissionError is a PASS -- it discloses nothing and refuses earlier than a filtered 0",
)
report(
	all(r["enforcement"] == "denied" for r in denied.values()),
	"...and is recorded as 'denied', so a change of enforcement layer stays VISIBLE rather than silently normalised",
)
report(
	all("table layer" in r["reason"] for r in denied.values()),
	"...with a reason naming the layer that refused",
)

broken = rerun("broken")
report(
	all(r["verdict"] == "NEEDS REVIEW" for r in broken.values()),
	"NOT LOOSENED: a NON-permission error (timeout) is still NEEDS REVIEW -- it yields no data too, but proves nothing about access",
)
report(
	all(r["enforcement"] == "inconclusive" for r in broken.values()),
	"...and is classified inconclusive rather than quietly counted as a denial",
)

# The one outcome that is an actual leak must be named as one, not lumped in
# with "something looked odd". Driven for real, not asserted against source.
leaked = rerun("leak")
report(
	all(r["verdict"] == "PERMISSION BREACH" for r in leaked.values()),
	"BREACH: rows reaching a restricted user gets its OWN verdict, not the same NEEDS REVIEW as a timeout",
)
report(
	all(r["enforcement"] == "breach" for r in leaked.values()),
	"BREACH: a non-zero restricted row count classifies as a breach, never as filtered",
)
report(
	all(r["restricted_rows"] > 0 for r in leaked.values()),
	"BREACH: the leaked row count is reported, so the size of the exposure is visible",
)

# apply_user_permissions is the second layer. When denial happens at the
# table layer the query never runs, so this run does not exercise row
# filtering at all -- the setting is then the only evidence it still exists.
denied_no_row_filter = rerun("deny", apply_user_permissions=0)
report(
	all(r["verdict"] == "NEEDS REVIEW" for r in denied_no_row_filter.values()),
	"DEFENCE IN DEPTH: table-layer denial with apply_user_permissions OFF is NOT a clean GO -- "
	"row filtering is then both unproven by this run and disabled",
)
filtered_no_setting = rerun("filter", apply_user_permissions=0)
report(
	all(r["enforcement"] == "filtered" for r in filtered_no_setting.values()),
	"...whereas a run that actually observed row-level filtering still reports what it saw",
)

# The control read is what turns a restricted result into evidence. Without
# it, a query broken or empty for EVERYONE reads as a clean denial.
empty_table = rerun("empty")
report(
	all(r["verdict"] == "NEEDS REVIEW" for r in empty_table.values()),
	"CONTROL READ: 0 restricted rows with 0 control rows is NEEDS REVIEW -- an empty table is not proof of filtering",
)
report(
	all("control read" in r["reason"] for r in empty_table.values()),
	"...and the reason says the control read is what was missing, not the permission model",
)

State.enforcement_layer = "filter"
State.singles["Insights Settings"]["apply_user_permissions"] = 1

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
