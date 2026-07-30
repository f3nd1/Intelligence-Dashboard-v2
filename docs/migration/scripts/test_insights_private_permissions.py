"""Go/no-go test: does a PRIVATE (is_public=0) Insights Chart v3/Query v3
actually enforce real per-user Frappe permissions when embedded, or only
when it happens to also be shared?

Written after reading the real, unabridged Insights v3.12.2 source --
insights/permissions.py, insights/api/__init__.py (`get_doc`,
`run_doc_method`, `_execute_doc_method`, `is_public_method`),
insights/insights/doctype/insights_table_v3/insights_table_v3.py
(`apply_user_permissions`), insights/insights/doctype/insights_query_v3/
insights_query_v3.py (`execute`) -- rather than assuming from the earlier
pilot's public-link-only findings. Two genuinely independent permission
layers exist and this script tests both separately, because testing only
one gives a misleading signal:

LAYER 1 -- document access. Can the user open the Chart/Dashboard/Query
record at all? Governed entirely by InsightsPermissions
(insights/permissions.py): ownership, DocShare, Workbook access, or
Team-based "Insights Resource Permission" grants. This has NOTHING to do
with Student Applicant permission -- it's Insights' own, separate sharing
system. A user can fail here regardless of their Student Applicant access,
which would look like a permission win but proves nothing about Layer 2.
`insights.api.get_doc` (insights/api/__init__.py) is a thin wrapper around
`frappe.client.get`, which calls `doc.has_permission("read")` -- for a
private (non-public) record that raises `frappe.PermissionError` and
`get_doc` re-raises it unchanged; only for a genuinely public record does
it fall back to an unchecked `frappe.get_doc(...).as_dict()`.

LAYER 2 -- row/column data filtering on query execution. In production
this runs through `insights.api.run_doc_method`, which calls
`_execute_doc_method` -- `doc.check_permission("read")` for a private
record (same Layer-1 gate as get_doc, this time on the Query document),
and only for a record confirmed public via `is_public()` AND whose method
is in `is_public_method`'s allowlist (`Insights Query v3`: `execute`,
`download_results`) does it retry with `ignore_permissions=True` *and* set
`frappe.flags.insights_for_public_access = True`, which is what disables
row filtering entirely (see below) -- confirming the public path bypasses
both layers. This script calls `doc.check_permission("read")` +
`doc.execute()` directly instead of going through `run_doc_method` --
that wrapper also calls `is_valid_http_method()`/`add_data_to_monitor()`,
which need a real `frappe.request` that doesn't exist in a bench console
session (raises `AttributeError('request')`, confirmed by an actual run).
Neither of those is part of what's being tested here; the direct call
exercises the same permission gate and the same `execute()` that matters.

Once past Layer 1, `Insights Query v3.execute()` (insights_query_v3.py)
builds its ibis pipeline via `InsightsTablev3.get_ibis_table()`
(insights_table_v3.py), which unconditionally applies
`apply_user_permissions()`: `frappe.has_permission(doctype, "read")` and
the same permission_query_conditions machinery frappe.get_list uses. If
the user can't read the DocType, the row filter becomes `t.filter(False)`
-- genuine zero-row enforcement, not a stub. Gated by `Insights
Settings.apply_user_permissions` (ships default=1, confirmed from the
DocType JSON -- but read the real value on this site below, not assumed)
and skipped only when `frappe.flags.insights_for_public_access` is set,
which (per the paragraph above) only happens on the public path this
script deliberately never exercises.

This is why the script explicitly SHARES the chart with the restricted test
user before testing Layer 2 -- otherwise a Layer-1 failure would mask
whatever Layer 2 does, and the whole point is to isolate the second
question. Also includes a positive-control step (grant the test user real
Student Applicant read access, re-run execute(), confirm real rows come
back) -- without that, an always-empty result would be indistinguishable
from "this is broken for everyone," which the earlier pilot's own
debugging saga is a good reminder not to assume away.

Usage -- paste into `bench --site <your-site> console` (confirm the real
site name via `ls sites/` first):

    exec(open("docs/migration/scripts/test_insights_private_permissions.py").read(), globals())

The trailing `globals()` matters: bare `exec(open(...).read())` inherits
whatever globals()/locals() are active at its own call site, and if bench
console evaluates pasted input from inside some internal method
(globals() != locals() there), a `def` function referencing a sibling
top-level name (as `is_shared_with_user` originally did with
TEST_USER_EMAIL, before that was changed to an explicit parameter)
resolves it via LOAD_GLOBAL against __globals__, which never received it
-- silent NameError. `exec(source, globals())` forces one shared
namespace instead of a two-dict split, closing off this whole class of
bug for every function here, not just the one already hit.

Creates one throwaway test user + role, cleaned up at the end
(CLEANUP_TEST_USER = True below; flip to False to leave it for further
manual poking). Every user-context switch uses frappe.set_user(), reset to
Administrator in a try/finally so a failure partway through doesn't leave
the console session running as the test user.
"""

import frappe

PILOT_TITLE = "Sophia Pilot - Student Applicants per Year"
TEST_USER_EMAIL = "insights-permission-test@ucc-intelligence.local"
TEST_ROLE = "Insights Permission Test Role"
CLEANUP_TEST_USER = True

results = {}


def stop(message):
	print("\nSTOP -- " + message)
	raise frappe.ValidationError(message)


# ============================================================
# Stage 0: find the pilot records, read the real site config
# ============================================================

print("=" * 70)
print("STAGE 0 -- discover pilot records and real site settings")
print("=" * 70)

chart_name = frappe.db.get_value("Insights Chart v3", {"title": PILOT_TITLE}, "name")
dashboard_name = frappe.db.get_value("Insights Dashboard v3", {"title": PILOT_TITLE}, "name")
if not chart_name:
	stop("No Insights Chart v3 found with title %r. Run create_insights_pilot.py first, "
		"or check the title if it was renamed." % PILOT_TITLE)

chart_doc = frappe.get_doc("Insights Chart v3", chart_name)
query_name = chart_doc.get("query") or chart_doc.get("data_query")
if not query_name:
	stop("Chart %s has neither `query` nor `data_query` set -- can't test execute()." % chart_name)

apply_user_permissions_setting = frappe.db.get_single_value("Insights Settings", "apply_user_permissions")
enable_permissions_setting = frappe.db.get_single_value("Insights Settings", "enable_permissions")

print("Chart: %s (workbook=%s)" % (chart_name, chart_doc.get("workbook")))
print("Dashboard: %s" % dashboard_name)
print("Backing query: %s" % query_name)
print("Insights Settings.apply_user_permissions = %r (ships default=1; this is the real site value)" % apply_user_permissions_setting)
print("Insights Settings.enable_permissions = %r (Team-based Data Source/Table visibility -- separate from the row filter above)" % enable_permissions_setting)
if not apply_user_permissions_setting:
	print("\nWARNING: apply_user_permissions is OFF on this site. Layer 2 (row filtering on "
		"query execution) will NOT be enforced regardless of what this script finds below -- "
		"that alone would be a reason to treat this path as not viable until it's turned on "
		"and re-tested, not a reason to stop the script (the rest still gives useful signal).")

results["chart_name"] = chart_name
results["dashboard_name"] = dashboard_name
results["query_name"] = query_name
results["apply_user_permissions_setting"] = bool(apply_user_permissions_setting)
results["enable_permissions_setting"] = bool(enable_permissions_setting)


# ============================================================
# Stage 1: make the chart/dashboard/query genuinely private
# ============================================================

print("\n" + "=" * 70)
print("STAGE 1 -- confirm is_public=0 (private, not the public link)")
print("=" * 70)

if dashboard_name:
	dash = frappe.get_doc("Insights Dashboard v3", dashboard_name)
	if dash.get("is_public"):
		dash.is_public = 0
		dash.share_link = None
		dash.save(ignore_permissions=True)
		frappe.db.commit()
	print("Dashboard %s is_public = %s" % (dashboard_name, frappe.db.get_value("Insights Dashboard v3", dashboard_name, "is_public")))
else:
	print("No dashboard found -- testing the Chart/Query directly, which were never made public anyway.")


# ============================================================
# Stage 2: Administrator -- confirm the baseline still works
# ============================================================

print("\n" + "=" * 70)
print("STAGE 2 -- Administrator, insights.api.get_doc (expected: succeeds)")
print("=" * 70)

from insights.api import get_doc as insights_get_doc  # noqa: E402

frappe.set_user("Administrator")
try:
	admin_doc = insights_get_doc("Insights Chart v3", chart_name)
	print("PASS: Administrator got the chart doc (title=%r)" % admin_doc.get("title"))
	results["admin_get_doc"] = "success"
except Exception as e:
	print("UNEXPECTED FAIL: Administrator could not fetch the chart: %s" % e)
	results["admin_get_doc"] = "failed: %s" % e


# ============================================================
# Stage 3: create a genuinely restricted test user
# ============================================================

print("\n" + "=" * 70)
print("STAGE 3 -- create a test user with confirmed zero Student Applicant access")
print("=" * 70)

if not frappe.db.exists("Role", TEST_ROLE):
	role = frappe.new_doc("Role")
	role.role_name = TEST_ROLE
	role.desk_access = 1
	role.insert(ignore_permissions=True)
	frappe.db.commit()
	print("Created role %s (no permissions assigned to it anywhere)" % TEST_ROLE)
else:
	print("Reusing existing role %s" % TEST_ROLE)

if not frappe.db.exists("User", TEST_USER_EMAIL):
	user = frappe.new_doc("User")
	user.email = TEST_USER_EMAIL
	user.first_name = "Insights Permission Test"
	user.send_welcome_email = 0
	user.append("roles", {"role": TEST_ROLE})
	user.insert(ignore_permissions=True)
	frappe.db.commit()
	print("Created test user %s" % TEST_USER_EMAIL)
else:
	print("Reusing existing test user %s" % TEST_USER_EMAIL)

can_read_applicant = frappe.has_permission("Student Applicant", "read", user=TEST_USER_EMAIL)
print("frappe.has_permission('Student Applicant', 'read', user=%r) = %s" % (TEST_USER_EMAIL, can_read_applicant))
if can_read_applicant:
	stop(
		"The test user unexpectedly HAS Student Applicant read access (perhaps via a role "
		"with broad default permissions, or User Permission rules). Pick a different role/user "
		"before continuing -- this test is meaningless without a confirmed-zero-access user."
	)
results["test_user_has_student_applicant_access_before"] = can_read_applicant


# ============================================================
# Stage 4: Layer 1, before sharing -- the honest default state
# ============================================================

print("\n" + "=" * 70)
print("STAGE 4 -- restricted user, insights.api.get_doc, BEFORE any Insights-side sharing")
print("(expected: fails -- Layer 1 blocks by default, same as any unshared Frappe document)")
print("=" * 70)

frappe.set_user(TEST_USER_EMAIL)
try:
	unshared_doc = insights_get_doc("Insights Chart v3", chart_name)
	print("UNEXPECTED: restricted user got the chart doc with no sharing set up at all: %r" % unshared_doc.get("title"))
	results["restricted_get_doc_before_share"] = "success (unexpected)"
except Exception as e:
	print("Blocked as expected (Layer 1, no sharing grant): %s" % e)
	results["restricted_get_doc_before_share"] = "blocked: %s" % e
finally:
	frappe.set_user("Administrator")


# ============================================================
# Stage 5: grant Layer-1 access via DocShare, confirm it now works
# ============================================================

print("\n" + "=" * 70)
print("STAGE 5 -- share the chart (and its query) with the test user, re-test get_doc")
print("(expected: succeeds -- proves the DocShare mechanism itself works as documented)")
print("=" * 70)

import frappe.share  # noqa: E402


def is_shared_with_user(dt, dn, user_email):
	# frappe.share.get_users(doctype, name) takes no `user` filter -- it returns every
	# share for the document, so filter for our test user here. Takes user_email as an
	# explicit arg rather than closing over TEST_USER_EMAIL -- bench console's exec()
	# doesn't reliably keep top-level names visible as free variables inside a def.
	return any(u.user == user_email for u in frappe.share.get_users(dt, dn))


for dt, dn in [("Insights Chart v3", chart_name), ("Insights Query v3", query_name)] + (
	[("Insights Dashboard v3", dashboard_name)] if dashboard_name else []
):
	if not is_shared_with_user(dt, dn, TEST_USER_EMAIL):
		frappe.share.add(dt, dn, user=TEST_USER_EMAIL, read=1)
frappe.db.commit()

frappe.set_user(TEST_USER_EMAIL)
try:
	shared_doc = insights_get_doc("Insights Chart v3", chart_name)
	print("PASS: restricted user now gets the chart doc after being shared: %r" % shared_doc.get("title"))
	results["restricted_get_doc_after_share"] = "success"
except Exception as e:
	print("STILL BLOCKED after explicit sharing -- this contradicts what the permissions.py "
		"source says should happen; worth a closer look before trusting anything below: %s" % e)
	results["restricted_get_doc_after_share"] = "blocked: %s" % e
finally:
	frappe.set_user("Administrator")


# ============================================================
# Stage 6: Layer 2 -- the real question. Does execute() filter rows?
# ============================================================

print("\n" + "=" * 70)
print("STAGE 6 -- restricted-but-now-shared user calls Query.execute() directly")
print("(the real data-fetch path -- expected, if apply_user_permissions is genuinely")
print(" enforced: zero rows, not real Student Applicant data)")
print("=" * 70)

frappe.set_user(TEST_USER_EMAIL)
try:
	# insights.api.run_doc_method (the real HTTP entry point) calls is_valid_http_method()
	# and add_data_to_monitor(), both of which need a real frappe.request -- unavailable in
	# bench console (AttributeError('request') from werkzeug's Local.__getattr__). Neither
	# is part of what we're testing, so call the same Layer-1 gate + the method directly.
	query_doc = frappe.get_doc("Insights Query v3", query_name)
	query_doc.check_permission("read")
	exec_result = query_doc.execute()
	row_count = len(exec_result.get("rows") or [])
	print("execute() succeeded, returned %d row(s)." % row_count)
	if row_count == 0:
		print("PASS (tentative -- see Stage 7's control check): zero rows for a user with no "
			"Student Applicant access. Consistent with apply_user_permissions working.")
	else:
		print("FAIL: real data returned (%d rows) to a user confirmed to have zero Student "
			"Applicant permission. This is the outcome that would rule out the embed approach." % row_count)
		print("Sample row:", exec_result["rows"][0])
	results["restricted_execute_row_count"] = row_count
except frappe.PermissionError as e:
	print("Blocked at check_permission('read') on the Query document itself (Layer 1 on the "
		"Query, not the Chart) -- unexpected after Stage 5's sharing succeeded on the Chart; "
		"the Query record itself may need its own explicit share. Detail: %s" % e)
	results["restricted_execute_row_count"] = "blocked_at_query_permission: %s" % e
except Exception as e:
	print("execute() raised an unexpected error: %s" % e)
	results["restricted_execute_row_count"] = "error: %s" % e
finally:
	frappe.set_user("Administrator")


# ============================================================
# Stage 7: positive control -- grant real Student Applicant access, re-run
# ============================================================

print("\n" + "=" * 70)
print("STAGE 7 -- control: grant the test user REAL Student Applicant read access, re-run execute()")
print("(expected: real rows now come back -- proves Stage 6's zero-row result, if any, was")
print(" actually permission-driven and not just 'this is broken for everyone')")
print("=" * 70)

if not frappe.db.exists("Has Role", {"parent": TEST_USER_EMAIL, "role": "System Manager"}):
	test_user_doc = frappe.get_doc("User", TEST_USER_EMAIL)
	test_user_doc.append("roles", {"role": "System Manager"})
	test_user_doc.save(ignore_permissions=True)
	frappe.db.commit()
	print("Granted System Manager to the test user as the simplest way to get real Student "
		"Applicant read access for this control step (broader than ideal, fine for a throwaway "
		"test user that gets deleted below).")

frappe.clear_cache(user=TEST_USER_EMAIL)
can_read_applicant_now = frappe.has_permission("Student Applicant", "read", user=TEST_USER_EMAIL)
print("frappe.has_permission('Student Applicant', 'read', user=%r) now = %s" % (TEST_USER_EMAIL, can_read_applicant_now))

frappe.set_user(TEST_USER_EMAIL)
try:
	query_doc = frappe.get_doc("Insights Query v3", query_name)
	query_doc.check_permission("read")
	control_result = query_doc.execute()
	control_row_count = len(control_result.get("rows") or [])
	print("Control execute() returned %d row(s)." % control_row_count)
	results["control_execute_row_count"] = control_row_count
except Exception as e:
	print("Control execute() raised an error: %s" % e)
	results["control_execute_row_count"] = "error: %s" % e
finally:
	frappe.set_user("Administrator")


# ============================================================
# Stage 8: verdict + cleanup
# ============================================================

print("\n" + "=" * 70)
print("STAGE 8 -- verdict")
print("=" * 70)
print(results)

restricted_rows = results.get("restricted_execute_row_count")
control_rows = results.get("control_execute_row_count")
if isinstance(restricted_rows, int) and isinstance(control_rows, int):
	if restricted_rows == 0 and control_rows > 0:
		print("\nGO signal: the restricted user got 0 rows, the same user with real Student "
			"Applicant access got %d rows. apply_user_permissions is genuinely filtering row data "
			"on private query execution, not just gating document visibility." % control_rows)
	elif restricted_rows > 0:
		print("\nNO-GO signal: the restricted user got real data (%d rows) despite confirmed zero "
			"Student Applicant permission. Embedding private Insights charts would leak data past "
			"ucc_dashboard_access's gating." % restricted_rows)
	elif control_rows == 0:
		print("\nINCONCLUSIVE: even the control (with real permission) got 0 rows -- something else "
			"is filtering everything (empty table, a stricter condition than DocType-level read, "
			"or a bug), not permission enforcement specifically. Needs investigation before trusting "
			"Stage 6's zero-row result as a real permission signal.")
else:
	print("\nINCONCLUSIVE: one or both execute() calls didn't return a clean row count -- read the "
		"per-stage output above for what actually happened before drawing a conclusion.")

if CLEANUP_TEST_USER:
	for dt, dn in [("Insights Chart v3", chart_name), ("Insights Query v3", query_name)] + (
		[("Insights Dashboard v3", dashboard_name)] if dashboard_name else []
	):
		if is_shared_with_user(dt, dn, TEST_USER_EMAIL):
			frappe.share.remove(dt, dn, TEST_USER_EMAIL)
	if frappe.db.exists("User", TEST_USER_EMAIL):
		frappe.delete_doc("User", TEST_USER_EMAIL, ignore_permissions=True, force=True)
	if frappe.db.exists("Role", TEST_ROLE):
		frappe.delete_doc("Role", TEST_ROLE, ignore_permissions=True, force=True)
	frappe.db.commit()
	print("\nTest user, role, and share grants cleaned up.")
else:
	print("\nCLEANUP_TEST_USER is False -- test user %s and role %s left in place for further "
		"manual poking." % (TEST_USER_EMAIL, TEST_ROLE))
