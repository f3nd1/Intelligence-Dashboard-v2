"""Runs monitoring rules and records what they found (CLAUDE.md Phase 11).

The engine does the querying, the deduplication and the bookkeeping. It
never decides whether a record passes -- that is rule_registry.py's pure
evaluators, so the pass/fail decision stays deterministic and reviewable
(CLAUDE.md §11: "the pass/fail decision should remain deterministic").

Idempotence is the property that matters, and it is a real requirement, not
a nicety: a scheduled rule runs every day against mostly the same records.
Re-running must not accumulate duplicates. So findings are keyed on
`rule_id::doctype::record`:

    still failing, finding open      -> touch it (count++, last_seen_run)
    still failing, finding resolved  -> REOPEN it, same row
    now passing,   finding open      -> resolve it
    now passing,   no finding        -> nothing
    still failing, finding suppressed-> leave it suppressed

A suppressed finding is never silently resurrected -- someone recorded a
reason for suppressing it, and a rerun is not new information.

Permissions: rules read with ignore_permissions=True, deliberately and
narrowly. A monitoring run is institutional housekeeping executed by the
scheduler, not a user browsing records: it must see every record in scope
or its counts are wrong in a way nobody can detect. What it produces is a
`UCC Monitoring Finding` naming a DocType and a record id -- and THAT is
permission-gated normally, so a user only ever sees findings they are
allowed to see, and opening one still goes through the target record's own
permissions. The bypass is on the counting, never on the disclosure.
"""

import frappe

from ucc_intelligence.monitoring import rule_registry

# A rule that would examine more than this has almost certainly been pointed
# at the wrong DocType, and a runaway scan belongs in a worker's log, not in
# a silent full-table read.
MAX_RECORDS_PER_RULE = 20000


def finding_key(rule_id, doctype, record):
	return "%s::%s::%s" % (rule_id, doctype, record)


def get_rule_doc(rule_id):
	"""The operational record for a rule, created from the registry on first
	use so an administrator has something to enable/disable and assign an
	owner to without a deploy."""
	definition = rule_registry.RULES[rule_id]
	if frappe.db.exists("UCC Monitoring Rule", rule_id):
		return frappe.get_doc("UCC Monitoring Rule", rule_id)

	doc = frappe.get_doc({
		"doctype": "UCC Monitoring Rule",
		"rule_id": rule_id,
		"title": definition["title"],
		"purpose": definition["purpose"],
		"target_doctype": definition["target_doctype"],
		"severity": definition["severity"],
		"remediation": definition.get("remediation"),
		"rule_version": definition["version"],
		"enabled": 1,
	})
	doc.insert(ignore_permissions=True)
	return doc


def load_target_rows(definition, effective_date):
	filters = {}
	if effective_date:
		filters["creation"] = [">=", effective_date]
	return frappe.get_all(
		definition["target_doctype"],
		filters=filters,
		fields=definition["fields"],
		limit_page_length=MAX_RECORDS_PER_RULE,
		ignore_permissions=True,
	)


def open_findings_for(rule_id):
	rows = frappe.get_all(
		"UCC Monitoring Finding",
		filters={"rule": rule_id},
		fields=["name", "finding_key", "status"],
		limit_page_length=0,
		ignore_permissions=True,
	)
	return {row["finding_key"]: row for row in rows}


def run_rule(rule_id):
	"""Evaluate one rule over its target DocType and reconcile the findings.
	Returns the run's counts. Never raises: a failing rule records a failed
	run rather than taking down the whole scheduled batch."""
	if rule_id not in rule_registry.RULES:
		frappe.throw(frappe._("Unknown monitoring rule: {0}").format(rule_id))

	definition = rule_registry.RULES[rule_id]
	rule_doc = get_rule_doc(rule_id)

	run = frappe.get_doc({
		"doctype": "UCC Monitoring Run",
		"rule": rule_id,
		"started_at": frappe.utils.now(),
		"status": "Running",
		"rule_version": definition["version"],
	})
	run.insert(ignore_permissions=True)

	if not rule_doc.enabled:
		run.status = "Completed"
		run.finished_at = frappe.utils.now()
		run.error_message = "Rule is disabled; no records were evaluated."
		run.save(ignore_permissions=True)
		return summarise(run)

	try:
		# Date-sensitive rules compare against today. Injected here rather than
		# read inside a rule, so rules stay pure functions and stay testable
		# without freezing the clock.
		rule_registry.set_today(frappe.utils.today())
		rows = load_target_rows(definition, rule_doc.effective_date)
		existing = open_findings_for(rule_id)
		evaluate = definition["evaluate"]

		failing_keys = set()
		for row in rows:
			detail = evaluate(row)
			if not detail:
				continue
			key = finding_key(rule_id, definition["target_doctype"], row["name"])
			failing_keys.add(key)
			record_finding(run, rule_doc, definition, existing.get(key), key, row["name"], detail)

		resolve_absent(run, existing, failing_keys)

		run.records_evaluated = len(rows)
		run.status = "Completed"
	except Exception as error:
		run.status = "Failed"
		# The message, not the traceback: a run row is operational history,
		# read by process owners, and CLAUDE.md §12.4 wants an error
		# reference rather than a stack trace in stored records.
		run.error_message = frappe.utils.cstr(error)[:500]
		frappe.log_error(title="UCC monitoring rule failed: %s" % rule_id)

	run.finished_at = frappe.utils.now()
	run.save(ignore_permissions=True)
	return summarise(run)


def record_finding(run, rule_doc, definition, existing, key, record_name, detail):
	if existing is None:
		frappe.get_doc({
			"doctype": "UCC Monitoring Finding",
			"rule": definition["rule_id"],
			"finding_key": key,
			"target_doctype": definition["target_doctype"],
			"target_record": record_name,
			"detail": detail,
			"status": "Open",
			"severity": rule_doc.severity or definition["severity"],
			"responsible_role": rule_doc.responsible_role,
			"first_seen_run": run.name,
			"last_seen_run": run.name,
			"occurrence_count": 1,
			"rule_version": definition["version"],
		}).insert(ignore_permissions=True)
		run.findings_opened = (run.findings_opened or 0) + 1
		return

	if existing["status"] == "Suppressed":
		# Someone recorded a reason. A rerun is not new information.
		return

	doc = frappe.get_doc("UCC Monitoring Finding", existing["name"])
	reopened = doc.status == "Resolved"
	doc.status = "Open"
	doc.detail = detail
	doc.last_seen_run = run.name
	doc.occurrence_count = (doc.occurrence_count or 0) + 1
	doc.rule_version = definition["version"]
	if reopened:
		doc.resolved_at = None
	doc.save(ignore_permissions=True)
	if reopened:
		run.findings_reopened = (run.findings_reopened or 0) + 1


def resolve_absent(run, existing, failing_keys):
	"""A finding whose record now passes is resolved, not deleted -- the
	history of what was wrong and when it was fixed is the point."""
	for key, row in existing.items():
		if key in failing_keys or row["status"] != "Open":
			continue
		doc = frappe.get_doc("UCC Monitoring Finding", row["name"])
		doc.status = "Resolved"
		doc.resolved_at = frappe.utils.now()
		doc.last_seen_run = run.name
		doc.save(ignore_permissions=True)
		run.findings_resolved = (run.findings_resolved or 0) + 1


def summarise(run):
	return {
		"run": run.name,
		"rule": run.rule,
		"status": run.status,
		"records_evaluated": run.records_evaluated or 0,
		"findings_opened": run.findings_opened or 0,
		"findings_reopened": run.findings_reopened or 0,
		"findings_resolved": run.findings_resolved or 0,
		"error_message": run.error_message,
	}


def run_all_rules():
	"""Every enabled rule. This is what the scheduler calls -- one rule
	failing must not stop the rest, which is why run_rule swallows its own
	exceptions into a Failed run rather than propagating."""
	return [run_rule(rule_id) for rule_id in rule_registry.RULES]


# How often each rule is worth running. Scanning every DocType daily is
# wasteful for rules whose findings change slowly, and the QA calendar is a
# quarterly instrument -- running it daily would produce the same finding 90
# times. Anything unlisted defaults to daily.
RULE_CADENCE = {
	"student_log_background_required": "daily",
	"student_log_dummy_text": "daily",
	"quality_action_closure_evidence": "daily",
	"expiring_contract": "daily",
	"department_housekeeping": "weekly",
	"course_review_evidence": "weekly",
	"qa_calendar_record": "quarterly",
}


def rules_due(cadence):
	return [rule_id for rule_id in rule_registry.RULES
		if RULE_CADENCE.get(rule_id, "daily") == cadence]


def run_cadence(cadence):
	"""Scheduler entry point for one cadence. Gated on the settings toggle for
	the same reason scheduled_run is: enabling monitoring must be a deliberate
	act, not something that starts scanning on install."""
	if not monitoring_enabled():
		return {"skipped": "Monitoring is disabled in UCC Intelligence Settings."}
	due = rules_due(cadence)
	if not due:
		return {"cadence": cadence, "runs": []}
	return {"cadence": cadence, "runs": [run_rule(rule_id) for rule_id in due]}


def run_daily():
	return run_cadence("daily")


def run_weekly():
	return run_cadence("weekly")


def run_quarterly():
	"""Frappe has no quarterly cron, so this is registered monthly and
	self-limits: it runs only in the first month of a quarter. Cheaper than a
	custom scheduler and visible in one place."""
	if not monitoring_enabled():
		return {"skipped": "Monitoring is disabled in UCC Intelligence Settings."}
	month = int(frappe.utils.today().split("-")[1])
	if month not in (1, 4, 7, 10):
		return {"skipped": "Not the first month of a quarter (month %d)." % month}
	return run_cadence("quarterly")


def monitoring_enabled():
	"""`UCC Intelligence Settings.enable_monitoring`. Defaults to OFF when
	unreadable: monitoring reads every record in its target DocType, so the
	safe default for a settings fault is not to run, unlike conversation
	persistence where the safe default is to keep the existing behaviour."""
	try:
		return bool(frappe.get_single("UCC Intelligence Settings").enable_monitoring)
	except Exception:
		return False


def scheduled_run():
	"""Scheduler entry point. Gated on the settings toggle so enabling
	monitoring is a deliberate act, not something that starts scanning the
	moment the app is installed."""
	if not monitoring_enabled():
		return {"skipped": "Monitoring is disabled in UCC Intelligence Settings."}
	return {"runs": run_all_rules()}
