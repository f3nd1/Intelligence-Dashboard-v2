# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""The read/act layer behind the Operations workspace.

WHY THIS MODULE EXISTS
Monitoring and Document Search were both "engine only". The rules ran, the
findings were written, the chunker chunked, the retriever retrieved -- and
nobody could see any of it without opening Desk and knowing which DocType to
filter. An engine nobody can look at is not a feature, it is a scheduled job.

This is the layer that makes them usable: list what exists, say what state it
is in, and let someone act on it. It adds no new detection logic and no new
retrieval logic. Everything below reads or nudges what
`monitoring/engine.py` and `knowledge/ingestion.py` already do.

WHY BOTH IN ONE MODULE, AND ONE WORKSPACE
They are two halves of the same job -- "what does this institution need to
deal with, and what does it know" -- and both are small. Two workspace tabs
for two half-features would cost more navigation than they are worth. If
either grows, splitting is a rename, not a rewrite.

PERMISSIONS -- WHO SEES WHAT, AND WHY IT DIFFERS
  findings        frappe.get_list. A finding names a real record, so a user
                  sees exactly the findings whose DocType permissions they
                  hold. No ignore_permissions anywhere in the read path.
  acting on one   frappe.has_permission("UCC Monitoring Finding", "write").
                  Resolving a finding is a claim that something was dealt
                  with; it belongs to whoever owns the process, not to
                  anyone who can see it.
  running a rule  System Manager only, at the api.py layer. A run reads every
                  record in the target DocType, which is an administrative
                  act (monitoring/engine.py explains why).
  sources         frappe.get_list plus knowledge/retrieval.py's own
                  restricted-to-role filter, which is stricter.
  registering     write permission on UCC Knowledge Source.

NOTHING HERE CALLS AN EXTERNAL PROVIDER. Deliberately: this round was to
finish what exists, and every one of these surfaces has to work with AI off
(CLAUDE.md §8.5).

FIELD NAMES ARE READ FROM THE DocType JSON, NOT REMEMBERED (fixed 2026-08-03)
The first version of this module asked for `rule_title`, `first_seen`,
`last_seen`, `rules_run`, `findings_open`, `last_run`, `version` and
`resolution_note`. NONE of those exist. Felix got

    (1054, "Unknown column 'rule_title' in 'SELECT'")

the moment he opened the panel. That was named as an unverified risk in the
previous report and it was the right thing to flag, but flagging is not
checking: every one of those names was verifiable offline, in this repository,
by opening the DocType's own JSON. It was laziness dressed as caution.

The real fields, from the JSON:

    UCC Monitoring Finding  rule, finding_key, target_doctype, target_record,
                            detail, status, severity, responsible_role,
                            first_seen_run, last_seen_run, occurrence_count,
                            resolved_at, suppression_reason, rule_version
    UCC Monitoring Run      rule, started_at, finished_at, status,
                            records_evaluated, findings_opened,
                            findings_reopened, findings_resolved,
                            rule_version, error_message
    UCC Monitoring Rule     rule_id, title, purpose, target_doctype, severity,
                            responsible_role, enabled, rule_version,
                            effective_date, remediation   (NO last_run)
    UCC Knowledge Source    title, source_type, attached_file, owner_department,
                            classification, permission_role, document_version,
                            effective_date, review_date, is_active,
                            superseded_by, content_checksum, sync_status,
                            last_indexed_at, chunk_count

`tools/test_operations.py` now reads those JSON files and asserts every field
this module requests really exists, so the next wrong name fails here rather
than on Felix's screen.
"""

import json

import frappe

FINDING_DOCTYPE = "UCC Monitoring Finding"
RUN_DOCTYPE = "UCC Monitoring Run"
RULE_DOCTYPE = "UCC Monitoring Rule"
SOURCE_DOCTYPE = "UCC Knowledge Source"
CHUNK_DOCTYPE = "UCC Knowledge Chunk"

FINDING_STATUSES = ("Open", "Resolved", "Suppressed")
SEVERITIES = ("High", "Medium", "Low")
MAX_ROWS = 200


def _text(value):
	return frappe.utils.cstr(value or "").strip()


def can_manage_findings():
	return bool(frappe.has_permission(FINDING_DOCTYPE, "write"))


def can_manage_sources():
	return bool(frappe.has_permission(SOURCE_DOCTYPE, "write"))


# --- monitoring -------------------------------------------------------------

def rules():
	"""Every rule the app knows, with whatever the site has recorded about it.

	The registry is the source of truth for what a rule IS -- its target, its
	severity, its remediation text -- because that is version-controlled code
	and cannot be edited into an inconsistent state. The DocType only carries
	what an administrator legitimately changes: whether it is enabled, and when
	it last ran. Merging them here means a rule always describes itself
	correctly even if its DocType record was never created.
	"""
	from ucc_intelligence.monitoring import rule_registry

	stored = {}
	try:
		for row in frappe.get_all(RULE_DOCTYPE,
				fields=["name", "rule_id", "enabled", "severity", "rule_version"],
				limit_page_length=0) or []:
			stored[row.get("rule_id") or row.get("name")] = row
	except Exception:
		stored = {}

	out = []
	for rule_id, definition in sorted(rule_registry.RULES.items()):
		record = stored.get(rule_id) or {}
		out.append({
			"rule_id": rule_id,
			"title": definition.get("title") or rule_id,
			"purpose": definition.get("purpose") or "",
			"target_doctype": definition.get("target_doctype") or "",
			"severity": record.get("severity") or definition.get("severity") or "Medium",
			"remediation": definition.get("remediation") or "",
			"version": definition.get("version") or "",
			# A rule with no record has never been configured. Reporting that
			# as "enabled: False" would be a guess about intent; reporting it
			# as unconfigured is what is actually true.
			"configured": bool(record),
			"enabled": bool(record.get("enabled")) if record else False,
			# UCC Monitoring Rule has no last_run field. When a rule last ran
			# is a fact about RUNS, so it is read from there rather than
			# denormalised onto the rule -- and asking for a column that does
			# not exist is what broke this panel in the first place.
			"last_run": last_run_of(rule_id),
			"open_findings": open_count(rule_id),
		})
	return out


def last_run_of(rule_id):
	"""When this rule last ran, from the run records themselves."""
	try:
		rows = frappe.get_all(RUN_DOCTYPE, filters={"rule": rule_id},
			fields=["started_at"], order_by="started_at desc", limit_page_length=1) or []
	except Exception:
		return ""
	return rows[0].get("started_at") if rows else ""


def open_count(rule_id):
	"""How many open findings this rule has, as THIS user may see them."""
	try:
		return len(frappe.get_list(FINDING_DOCTYPE,
			filters={"rule": rule_id, "status": "Open"},
			fields=["name"], limit_page_length=MAX_ROWS) or [])
	except Exception:
		return 0


def findings(status="Open", rule=None, severity=None, limit=100):
	"""Findings this user is allowed to see, newest first.

	get_list, never get_all: a finding names a real record, so who may see it
	is exactly who may see that record's DocType.
	"""
	status = _text(status) or "Open"
	if status not in FINDING_STATUSES and status != "All":
		status = "Open"
	filters = {}
	if status != "All":
		filters["status"] = status
	if _text(rule):
		filters["rule"] = _text(rule)
	if _text(severity) in SEVERITIES:
		filters["severity"] = _text(severity)
	try:
		limit = max(1, min(int(limit or 100), MAX_ROWS))
	except (TypeError, ValueError):
		limit = 100
	try:
		rows = frappe.get_list(
			FINDING_DOCTYPE, filters=filters,
			fields=["name", "rule", "status", "severity", "target_doctype",
				"target_record", "detail", "occurrence_count", "responsible_role",
				"first_seen_run", "last_seen_run", "modified"],
			order_by="modified desc", limit_page_length=limit) or []
	except Exception as error:
		return {"ok": False, "findings": [], "message": _text(error),
			"can_manage": can_manage_findings()}
	# The finding stores the rule ID; the human-readable title lives in the
	# version-controlled registry. Joined here so the table can show a sentence
	# instead of `student_log_background_required`.
	from ucc_intelligence.monitoring import rule_registry

	for row in rows:
		definition = rule_registry.RULES.get(row.get("rule")) or {}
		row["rule_title"] = definition.get("title") or row.get("rule") or ""
		row["remediation"] = definition.get("remediation") or ""
	return {"ok": True, "findings": rows, "status": status,
		"can_manage": can_manage_findings()}


def set_finding_status(finding, status, note=None):
	"""Resolve, suppress or reopen one finding.

	Suppressing requires a note. A suppressed finding is never resurrected by a
	later run (monitoring/engine.py:17), so it is the one status that silences
	something indefinitely -- and an unexplained silence is not auditable.
	"""
	status = _text(status)
	if status not in FINDING_STATUSES:
		frappe.throw(frappe._("Unknown finding status."))
	if not can_manage_findings():
		raise frappe.PermissionError(
			"You do not have permission to change monitoring findings.")
	note = _text(note)
	if status == "Suppressed" and not note:
		frappe.throw(frappe._("Say why this finding is being suppressed."))

	doc = frappe.get_doc(FINDING_DOCTYPE, _text(finding))
	before = doc.get("status")
	doc.status = status
	# The field is `suppression_reason` -- read from the DocType JSON, not
	# recalled. has_field still guards it, because a DocType can be altered.
	if note and doc.meta.has_field("suppression_reason"):
		doc.suppression_reason = note
	if status == "Resolved" and doc.meta.has_field("resolved_at"):
		doc.resolved_at = frappe.utils.now()
	doc.save()
	frappe.logger("ucc_intelligence").info(
		"monitoring finding %s %s -> %s by %s" % (doc.name, before, status, frappe.session.user))
	return {"ok": True, "finding": doc.name, "status": status, "was": before}


def runs(limit=10):
	"""Recent monitoring runs, so "did it run" is answerable without Desk."""
	try:
		limit = max(1, min(int(limit or 10), 50))
	except (TypeError, ValueError):
		limit = 10
	try:
		return frappe.get_list(RUN_DOCTYPE,
			fields=["name", "rule", "status", "started_at", "finished_at",
				"records_evaluated", "findings_opened", "findings_reopened",
				"findings_resolved", "error_message"],
			order_by="creation desc", limit_page_length=limit) or []
	except Exception:
		return []


def monitoring_overview():
	"""Everything the Monitoring panel needs, in one call."""
	from ucc_intelligence.monitoring import engine

	try:
		enabled = bool(engine.monitoring_enabled())
	except Exception:
		enabled = False
	open_rows = findings("Open", limit=MAX_ROWS)
	by_severity = {severity: 0 for severity in SEVERITIES}
	for row in open_rows.get("findings") or []:
		key = row.get("severity")
		if key in by_severity:
			by_severity[key] += 1
	return {
		"ok": True,
		"enabled": enabled,
		"rules": rules(),
		"open_by_severity": by_severity,
		"open_total": len(open_rows.get("findings") or []),
		"runs": runs(5),
		"can_manage": can_manage_findings(),
	}


# --- document knowledge -----------------------------------------------------

def sources(limit=100):
	"""Registered knowledge sources and their indexing state.

	Nothing is fabricated. With no documents registered this returns an empty
	list, and the panel says so -- an empty index that claims to hold policies
	would be worse than no panel at all.
	"""
	try:
		limit = max(1, min(int(limit or 100), MAX_ROWS))
	except (TypeError, ValueError):
		limit = 100
	try:
		rows = frappe.get_list(
			SOURCE_DOCTYPE,
			fields=["name", "title", "source_type", "owner_department",
				"classification", "effective_date", "review_date",
				"document_version", "is_active", "sync_status",
				"last_indexed_at", "superseded_by", "chunk_count"],
			order_by="modified desc", limit_page_length=limit) or []
	except Exception as error:
		return {"ok": False, "sources": [], "message": _text(error),
			"can_manage": can_manage_sources()}
	for row in rows:
		# chunk_count is stored on the source; counting rows is the fallback
		# for a source indexed before that field was populated.
		row["chunks"] = row.get("chunk_count") or chunk_count(row["name"])
		row["version"] = row.get("document_version") or ""
		row["last_indexed"] = row.get("last_indexed_at") or ""
	return {"ok": True, "sources": rows, "can_manage": can_manage_sources()}


def chunk_count(source_name):
	try:
		return len(frappe.get_list(CHUNK_DOCTYPE, filters={"source": source_name},
			fields=["name"], limit_page_length=MAX_ROWS) or [])
	except Exception:
		return 0


def knowledge_overview():
	"""Everything the Knowledge panel needs, in one call."""
	try:
		enabled = bool(frappe.get_single("UCC Intelligence Settings").enable_document_knowledge)
	except Exception:
		enabled = False
	listing = sources()
	rows = listing.get("sources") or []
	return {
		"ok": True,
		"enabled": enabled,
		"sources": rows,
		"total": len(rows),
		"indexed": len([row for row in rows if row.get("last_indexed")]),
		"stale": len([row for row in rows if (row.get("sync_status") or "") == "Stale"]),
		"chunks": sum(row.get("chunks") or 0 for row in rows),
		"can_manage": listing.get("can_manage"),
		"message": listing.get("message") or "",
	}


def add_source(title, source_type, text=None, attached_file=None, **fields):
	"""Register a document and index it in one step.

	The engine already had register_source() and index_source(); what it did
	not have was any way to reach them that was not a bench console. This is
	that way. Permission is the DocType's own -- no bypass.
	"""
	from ucc_intelligence.knowledge import ingestion

	if not can_manage_sources():
		raise frappe.PermissionError(
			"You do not have permission to register knowledge sources.")
	title = _text(title)
	if not title:
		frappe.throw(frappe._("A knowledge source needs a title."))
	if not _text(text) and not _text(attached_file):
		frappe.throw(frappe._("Paste the document text, or attach a file."))

	# register_source() ALREADY INDEXES -- it ends with index_source() and
	# returns {"ok", "indexed", "sections"|"message", "source"}. The first
	# version of this function indexed a second time and passed it the dict
	# rather than the name, which is why Felix's registration appeared to do
	# nothing: the real work had already happened, and the redundant call
	# failed silently into a swallowed exception.
	try:
		result = ingestion.register_source(
			title=title, source_type=_text(source_type) or "Policy",
			text=text, attached_file=attached_file, **fields)
	except Exception as error:
		# Never a silent no-op. A registration that fails says so.
		frappe.log_error(title="UCC knowledge registration failed",
			message="%s\n\n%s" % (title, frappe.get_traceback()))
		return {"ok": False, "indexed": False, "source": "", "message": _text(error)}

	if not isinstance(result, dict):
		result = {"ok": True, "indexed": True, "source": result}
	return {
		"ok": bool(result.get("ok", True)),
		"source": result.get("source") or "",
		"indexed": bool(result.get("indexed")),
		"sections": result.get("sections") or 0,
		"message": result.get("message") or "",
	}


def reindex(source=None):
	"""Re-index one source, or every stale one. Write permission required."""
	from ucc_intelligence.knowledge import ingestion

	if not can_manage_sources():
		raise frappe.PermissionError(
			"You do not have permission to re-index knowledge sources.")
	if _text(source):
		ingestion.index_source(_text(source))
		return {"ok": True, "reindexed": [_text(source)]}
	done = ingestion.reindex_stale()
	return {"ok": True, "reindexed": done if isinstance(done, list) else []}
