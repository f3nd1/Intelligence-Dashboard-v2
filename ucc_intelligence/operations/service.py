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
				fields=["name", "rule_id", "enabled", "last_run", "severity"],
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
			"last_run": record.get("last_run") or "",
			"open_findings": open_count(rule_id),
		})
	return out


def open_count(rule_id):
	"""How many open findings this rule has, as THIS user may see them."""
	try:
		return len(frappe.get_list(FINDING_DOCTYPE,
			filters={"rule_id": rule_id, "status": "Open"},
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
		filters["rule_id"] = _text(rule)
	if _text(severity) in SEVERITIES:
		filters["severity"] = _text(severity)
	try:
		limit = max(1, min(int(limit or 100), MAX_ROWS))
	except (TypeError, ValueError):
		limit = 100
	try:
		rows = frappe.get_list(
			FINDING_DOCTYPE, filters=filters,
			fields=["name", "rule_id", "rule_title", "status", "severity",
				"target_doctype", "target_record", "detail", "first_seen", "last_seen"],
			order_by="last_seen desc", limit_page_length=limit) or []
	except Exception as error:
		return {"ok": False, "findings": [], "message": _text(error),
			"can_manage": can_manage_findings()}
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
	if note and doc.meta.has_field("resolution_note"):
		doc.resolution_note = note
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
			fields=["name", "status", "started_at", "finished_at",
				"rules_run", "findings_open", "findings_resolved"],
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
				"classification", "effective_date", "review_date", "version",
				"is_active", "sync_status", "last_indexed", "superseded_by"],
			order_by="modified desc", limit_page_length=limit) or []
	except Exception as error:
		return {"ok": False, "sources": [], "message": _text(error),
			"can_manage": can_manage_sources()}
	for row in rows:
		row["chunks"] = chunk_count(row["name"])
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
	source = ingestion.register_source(
		title=title, source_type=_text(source_type) or "Policy",
		text=text, attached_file=attached_file, **fields)
	name = source if isinstance(source, str) else getattr(source, "name", None) or source
	result = {"ok": True, "source": name, "indexed": False}
	try:
		ingestion.index_source(name, text=text)
		result["indexed"] = True
	except Exception as error:
		# Registered but not indexed is a real, recoverable state -- and one
		# the panel shows -- so it is reported rather than rolled back.
		result["message"] = _text(error)
	return result


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
