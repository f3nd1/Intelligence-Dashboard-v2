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

DOCUMENT KNOWLEDGE IS NOT A SIDE FEATURE (framing corrected 2026-08-03)
An earlier version of this module and its UI described the knowledge base as
one screen's index. That is wrong, and Felix corrected it. Document Search is
one of the three pillars of the original design -- reasoning (OpenAI),
memory (Zep/Graphiti, deferred and not built), and Document Search -- which
together form the brain behind a single AI Gateway serving the criterion
dashboards, Ask UCC, monitoring and agents, reports and alerts. A document
registered here becomes part of what the WHOLE platform can draw on. The
on-page copy now says so. Whether it deserves its own place in the main
navigation rather than a panel inside Operations is Felix's call, not mine.
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

SETTINGS_DOCTYPE = "UCC Intelligence Settings"
# The gear used to make you CHOOSE between a Sophia page and the Frappe form,
# which meant three of the five sections were always somewhere you were not.
# This is the allowlist behind the one surface that now serves all five.
# Only the FIELD NAMES are stated here. Their types come from the DocType's own
# meta, for the same reason the monitoring field names now do: a type restated
# in a second place is a type that can drift, and `ai_provider` is a Select,
# which the first version of this list had confidently written down as Data.
SETTINGS_SECTIONS = (
	("ai", "AI and providers", ("enable_ai", "ai_provider", "ai_model",
		"max_output_tokens", "default_temperature", "ai_request_timeout_seconds")),
	("presentation", "Presentation", ("chart_palette",)),
	("knowledge", "Document knowledge", ("enable_document_knowledge",
		"enable_persistent_conversations")),
	("monitoring", "Monitoring", ("enable_monitoring",)),
)
SETTINGS_FIELDS = tuple(field for _key, _label, fields in SETTINGS_SECTIONS
	for field in fields)


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


# --- institution-wide settings: access, and monitoring rules ----------------
# Sections 2 and 4 of the settings split agreed on 2026-08-03. Sections 1, 3
# and 5 (AI provider, chart palette, knowledge policy) stay on the Frappe form
# for UCC Intelligence Settings -- they are plain fields and Frappe's own form
# renders them perfectly well. These two do not: access is a matrix and rules
# are a table, and both are unreadable as a stack of form fields.
#
# NO NEW PERMISSION CONCEPTS. Everything below surfaces what already exists:
# UCC Dashboard Access for criteria and Ask UCC modules, and write permission
# on the two DocTypes for editing tabs and acting on findings.

def access_overview():
	"""Who can see what, from the existing permission model only."""
	from ucc_intelligence.permissions import access

	try:
		response = access.build_response()
	except Exception as error:
		return {"ok": False, "message": _text(error)}
	criteria = response.get("criteria") or {}
	return {
		"ok": True,
		"criteria": [{"key": key, "visible": bool(criteria.get(key))}
			for key in sorted(criteria)],
		"modules": {key: bool(response.get(key))
			for key in ("ask_student_journey", "ask_recruitment_agent", "ask_quality_action")
			if key in response},
		# Read-only mirrors, so the whole model is legible in one place. These
		# are Frappe DocType permissions and are changed in Role Permission
		# Manager, not here -- stated rather than implied.
		"can_edit_tabs": bool(frappe.has_permission("UCC Analytics Tab", "write")),
		"can_manage_findings": can_manage_findings(),
		"can_manage_sources": can_manage_sources(),
		"note": ("Criterion and Ask UCC visibility comes from the UCC Dashboard Access "
			"records. Who may edit tabs or close findings is ordinary Frappe DocType "
			"permission, changed in Role Permission Manager."),
	}


def set_rule_config(rule_id, enabled=None, severity=None):
	"""Turn one rule on or off, or change its severity.

	The rule's DEFINITION stays in code -- what it looks at and what counts as
	a problem is not editable, because a rule an auditor cannot trust is not
	worth running. What an administrator legitimately changes is whether it
	runs and how loudly it reports, and that is what this writes.
	"""
	from ucc_intelligence.monitoring import rule_registry

	rule_id = _text(rule_id)
	if rule_id not in rule_registry.RULES:
		frappe.throw(frappe._("Unknown monitoring rule."))
	if not frappe.has_permission(RULE_DOCTYPE, "write"):
		raise frappe.PermissionError(
			"You do not have permission to change monitoring rules.")
	definition = rule_registry.RULES[rule_id]

	existing = frappe.get_all(RULE_DOCTYPE, filters={"rule_id": rule_id},
		fields=["name"], limit_page_length=1) or []
	if existing:
		doc = frappe.get_doc(RULE_DOCTYPE, existing[0]["name"])
	else:
		# First time this rule is configured. Seeded from the registry so the
		# record always describes the rule correctly.
		doc = frappe.new_doc(RULE_DOCTYPE)
		doc.rule_id = rule_id
		doc.title = definition.get("title") or rule_id
		doc.purpose = definition.get("purpose") or ""
		doc.target_doctype = definition.get("target_doctype") or ""
		doc.responsible_role = definition.get("responsible_role") or ""
		doc.remediation = definition.get("remediation") or ""
	doc.rule_version = definition.get("version") or ""
	if enabled is not None:
		doc.enabled = 1 if _text(enabled).lower() in ("1", "true", "yes", "on") else 0
	if _text(severity) in SEVERITIES:
		doc.severity = _text(severity)
	doc.save() if existing else doc.insert()
	return {"ok": True, "rule_id": rule_id,
		"enabled": bool(doc.enabled), "severity": doc.severity}


# --- one settings surface, all five sections --------------------------------

def platform_settings():
	"""Everything set once for the whole institution, in one call.

	System Manager only. These are institution-wide switches -- which provider
	answers, how warm the model runs, what the charts are coloured with, and
	whether monitoring runs at all. None of it is per-user, so nothing here is
	scoped to the caller; the gate is simply who may see it.
	"""
	frappe.only_for("System Manager")
	doc = frappe.get_single(SETTINGS_DOCTYPE)
	meta = frappe.get_meta(SETTINGS_DOCTYPE)
	sections = []
	for key, label, fields in SETTINGS_SECTIONS:
		rendered = []
		for fieldname in fields:
			df = meta.get_field(fieldname)
			if not df:
				# The field was renamed or removed. Skipping beats throwing:
				# the other four sections are still worth showing.
				continue
			rendered.append({
				"fieldname": fieldname,
				"fieldtype": df.fieldtype,
				"options": df.options or "",
				"value": doc.get(fieldname),
			})
		if rendered:
			sections.append({"key": key, "label": label, "fields": rendered})
	return {"ok": True, "sections": sections}


def save_platform_settings(values):
	"""Write the allowlisted settings, and only those.

	The allowlist is the whole point. A settings endpoint that writes whatever
	key it is handed is a write-any-field-on-a-Single endpoint, and this one is
	reachable from a browser. Anything not in SETTINGS_FIELDS is ignored in
	silence -- not an error, because a stale open tab sending an old field name
	should not fail the four that are still valid.
	"""
	frappe.only_for("System Manager")
	if isinstance(values, str):
		try:
			values = json.loads(values)
		except ValueError:
			frappe.throw(frappe._("Settings could not be read."))
	if not isinstance(values, dict):
		frappe.throw(frappe._("Settings could not be read."))

	doc = frappe.get_single(SETTINGS_DOCTYPE)
	meta = frappe.get_meta(SETTINGS_DOCTYPE)
	written = []
	for fieldname, value in values.items():
		if fieldname not in SETTINGS_FIELDS:
			continue
		df = meta.get_field(fieldname)
		if not df:
			continue
		if df.fieldtype == "Check":
			value = 1 if _text(value).lower() in ("1", "true", "yes", "on") else 0
		elif df.fieldtype == "Int":
			value = frappe.utils.cint(value)
		elif df.fieldtype == "Float":
			value = frappe.utils.flt(value)
		else:
			value = _text(value)
		doc.set(fieldname, value)
		written.append(fieldname)
	if written:
		doc.save()
		# Who changed an institution-wide switch is worth knowing later. The
		# names only -- the values are on the record itself, and one of these
		# fields sits next to a provider credential.
		frappe.logger("ucc_intelligence").info(
			"platform settings changed by %s: %s" % (frappe.session.user, ", ".join(written)))
	return {"ok": True, "written": written}
