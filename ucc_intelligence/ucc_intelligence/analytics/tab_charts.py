# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""What a person has put on one criterion tab: charts, their sizes, the tab's
own intro text, and which management questions they want to see.

WHY THIS REPLACED THE OLD CHART BOXES
The dashboard used to ship 222 fixed chart boxes across the seven criteria,
each hard-coded in the page's own LIVE_VISUAL_EXPANSION table and looked up in
a 113-entry registry. Only 16 of them ever had a real Insights query behind
them; the other 206 were blank. Boxes nobody chose, mostly showing nothing.

Now a tab starts with nothing and a "+ Add chart" button. A person picks a real
Insights query -- one they can already read -- and it is embedded on that tab,
at the size they choose, until they remove it.

WHERE IT LIVES -- ONE PLACE, SHARED BY EVERYONE

    DocType:  UCC Analytics Tab        (one record per criterion+tab,
                                        named "<criterion>::<tab>")
    charts            -> field `charts`             (JSON list of {chart,size})
    tab intro text    -> field `intro`              (Markdown subset)
    hidden questions  -> field `hidden_questions`   (JSON list of question ids)

It was per user, in `frappe.defaults`, until 2026-08-02. That was wrong and
Felix said so: Sophia is an institutional dashboard used as EduTrust evidence,
not a personal workspace. A chart the Quality Manager adds as evidence has to
be the chart the auditor sees. The old per-user records are migrated by
patches/v1_0/migrate_tab_config_to_shared.py, not abandoned.

WHO MAY CHANGE IT
Write permission on `UCC Analytics Tab` -- the same permission shape
`UCC Dashboard Access` already uses for dashboard configuration, so this is the
existing Sophia pattern rather than a new one, and the role can be widened in
Desk without a code change. can_edit() is the single gate; everyone else gets
the same view with `can_edit: False`, and the page does not render the controls
at all.

PERMISSIONS -- FOUR GATES, NONE OF THEM THE PICKER'S UI
  1. the criterion tab itself: ucc_dashboard_access must show it to this user
  2. WRITING anything: can_edit() -- write permission on UCC Analytics Tab
  3. the search: frappe.get_list applies read permission + user permissions,
     so a query the user cannot read is never offered
  4. every read afterwards: get_tab re-filters stored ids through the same list
     call, and chart_data() calls check_permission("read") before executing.
     Access revoked after a chart was added means it stops appearing -- a
     stored id is a preference, never a grant.

Gate 4 is why sharing the configuration does not share access to the DATA:
a chart on a shared tab still executes as the person looking at it, and simply
does not appear for someone who may not read its query.
"""

import json

import frappe

from ucc_intelligence.analytics.admission_intelligence_embed import clean_text, rows_to_chart_series
from ucc_intelligence.analytics import chart_presentation
from ucc_intelligence.analytics import tab_audit
from ucc_intelligence.permissions import access

# Only a record type we can actually EXECUTE and permission-check is offered.
#
# Insights v3 stores the executable thing as `Insights Query v3`: it is what
# build_admission_intelligence_embed.py creates, what the six admission charts
# run on, and what the bench permission test was run against
# (test_insights_private_permissions.py). `Insights Chart v3` is a presentation
# record whose execute() contract has never been checked on this bench, so it
# is deliberately not offered. Listing something we cannot run would put a
# broken card in front of a user who did nothing wrong.
CHART_DOCTYPE = "Insights Query v3"

CONFIG_DOCTYPE = "UCC Analytics Tab"

# The per-user store this replaced. Still named here because the migration
# patch reads it, and because a stale copy on a bench should be recognisable.
LEGACY_DEFAULTS_PREFIX = "ucc_sophia_tab_charts"

# A tab is a place to look at a few things, not a dumping ground. Bounded so a
# stored value stays small and a tab stays loadable.
MAX_PER_TAB = 12
MAX_INTRO_LENGTH = 4000
MAX_QUESTION_IDS = 60

# Card width, in columns of the tab's 12-column grid. Stored as the SPAN, not
# as a name: the size is now set by dragging a card's edge, which snaps to the
# grid, so any of 1..12 is reachable and "medium" no longer describes it.
#
# The four old names are still read, because tabs configured before the drag
# handle existed hold them. They are never written.
GRID_COLUMNS = 12
LEGACY_SIZE_SPANS = {"small": 3, "medium": 6, "large": 9, "full": 12}
DEFAULT_SPAN = 6

# Tab keys come from the page (criterion sub-sections such as "4.1.1", plus
# "overview"). Constrained so a caller cannot write an arbitrary defaults key.
TAB_CHARACTERS = set("abcdefghijklmnopqrstuvwxyz0123456789._-")


def _key(criterion, tab):
	"""The record name. autoname is format:{criterion}::{tab}, so the key and
	the name are the same thing and a duplicate cannot exist."""
	return "%s::%s" % (criterion, tab)


def can_edit():
	"""Whether this user may change how a tab is configured for everyone.

	Write permission on the config DocType itself -- the same shape
	`UCC Dashboard Access` uses. Not a hardcoded role: granting a Quality
	Manager the right to curate tabs is a Desk change, not a deployment.
	"""
	return bool(frappe.has_permission(CONFIG_DOCTYPE, "write"))


def _require_edit():
	if not can_edit():
		frappe.throw(
			frappe._("You do not have permission to change how this tab is set up for everyone."),
			frappe.PermissionError)


def _validated(criterion, tab):
	"""Reject anything that is not a real criterion and a plausible tab, then
	confirm this user is allowed to see that criterion at all."""
	criterion = clean_text(criterion)
	tab = clean_text(tab).lower()
	if criterion not in access.CRITERION_KEYS:
		frappe.throw(frappe._("Unknown criterion."), frappe.ValidationError)
	if not tab or len(tab) > 40 or set(tab) - TAB_CHARACTERS:
		frappe.throw(frappe._("Unknown tab."), frappe.ValidationError)
	if not access.build_response()["criteria"].get(criterion):
		frappe.throw(
			frappe._("This criterion is not available to your account."), frappe.PermissionError)
	return criterion, tab


def _span(item):
	"""This card's width in grid columns, from either shape it was ever stored
	in: a `span` integer now, or one of the four old size names before that."""
	span = item.get("span")
	try:
		span = int(span)
	except (TypeError, ValueError):
		span = LEGACY_SIZE_SPANS.get(item.get("size"), DEFAULT_SPAN)
	return max(1, min(span, GRID_COLUMNS))


def _blank():
	return {"charts": [], "intro": "", "questions": {"hidden": []}}


def _json_list(value):
	"""A stored JSON list, or an empty one. Unreadable is treated as absent
	rather than repaired -- a corrupt field should cost a tab its layout, not
	raise on every page load for every user."""
	try:
		parsed = json.loads(value or "[]")
	except (TypeError, ValueError):
		return []
	return parsed if isinstance(parsed, list) else []


def _stored(criterion, tab):
	"""One tab's shared configuration.

	Read with ignore_permissions for the same reason access.py reads
	`UCC Dashboard Access` that way, and documented here rather than inherited
	silently: this DocType holds interface configuration only -- which charts,
	what intro text, which questions to hide. It contains no institutional
	data, and every figure those charts and questions show is fetched
	separately, as the signed-in user, with its own permission check
	(chart_data() and the criterion engine). Everyone who can see a tab must be
	able to see how it is set up, or a shared configuration would be invisible
	to the people it is for. WRITING is gated by can_edit(); this is the read.
	"""
	config = _blank()
	name = _key(criterion, tab)
	try:
		if not frappe.db.exists(CONFIG_DOCTYPE, name):
			return config
		record = frappe.get_doc(CONFIG_DOCTYPE, name)
	except Exception:
		return config

	stored = {
		"charts": _json_list(record.get("charts")),
		"intro": record.get("intro") or "",
		"questions": {"hidden": _json_list(record.get("hidden_questions"))},
	}

	for item in (stored.get("charts") or [])[:MAX_PER_TAB]:
		if isinstance(item, str) and item:
			config["charts"].append({"chart": item, "span": DEFAULT_SPAN})
		elif isinstance(item, dict) and item.get("chart"):
			entry = {"chart": str(item["chart"]), "span": _span(item)}
			# Normalising to a fixed shape is what keeps a corrupt stored value
			# from reaching the page -- but an entry only carries keys named
			# here, so a new one has to be added deliberately. The palette is
			# re-validated rather than trusted: it came from storage, and
			# storage is editable in Desk.
			palette = chart_presentation.normalise_palette(item.get("palette"))
			if palette:
				entry["palette"] = palette
			config["charts"].append(entry)

	intro = stored.get("intro")
	if isinstance(intro, str):
		config["intro"] = intro[:MAX_INTRO_LENGTH]

	questions = stored.get("questions")
	if isinstance(questions, dict) and isinstance(questions.get("hidden"), list):
		config["questions"]["hidden"] = [
			str(v) for v in questions["hidden"] if isinstance(v, str) and v][:MAX_QUESTION_IDS]
	return config


def _store(criterion, tab, config):
	"""Write one tab's shared configuration.

	Only ever reached after _require_edit(). ignore_permissions is NOT used
	here -- the write goes through the DocType's own permission check as well,
	so the gate holds even if some future caller forgets to ask first.
	"""
	name = _key(criterion, tab)
	values = {
		"charts": json.dumps(config["charts"][:MAX_PER_TAB]),
		"intro": (config.get("intro") or "")[:MAX_INTRO_LENGTH],
		"hidden_questions": json.dumps(config["questions"]["hidden"][:MAX_QUESTION_IDS]),
	}
	if frappe.db.exists(CONFIG_DOCTYPE, name):
		record = frappe.get_doc(CONFIG_DOCTYPE, name)
		record.update(values)
		record.save()
		return
	record = frappe.new_doc(CONFIG_DOCTYPE)
	record.update(dict(values, criterion=criterion, tab=tab))
	record.insert()


def readable(names):
	"""Of these chart ids, the ones this user may read, mapped to their titles.

	frappe.get_list -- not get_all -- so permissions and user permissions both
	apply. This is what makes a stored id a preference rather than a grant.
	"""
	if not names:
		return {}
	rows = frappe.get_list(
		CHART_DOCTYPE, filters={"name": ["in", names]}, fields=["name", "title"],
		limit_page_length=len(names))
	return {row["name"]: row.get("title") or row["name"] for row in rows}


def search(term=None, limit=20):
	"""Insights queries this user can read, for the picker.

	Empty term lists the most recently modified, so the picker is useful before
	anyone types. Titles only: the query's internal name is a hash and means
	nothing to the person choosing.
	"""
	limit = max(1, min(int(limit or 20), 50))
	if not frappe.db.exists("DocType", CHART_DOCTYPE):
		return {"ok": False, "charts": [], "message":
			"Frappe Insights is not installed on this site, so there are no charts to add."}
	filters = {}
	term = clean_text(term)
	if term:
		filters["title"] = ["like", "%%%s%%" % term]
	rows = frappe.get_list(
		CHART_DOCTYPE, filters=filters, fields=["name", "title"],
		order_by="modified desc", limit_page_length=limit)
	# BOTH kinds are listed, each marked -- not charts only.
	#
	# The probe found 52 queries and 7 charts. Listing only the 7 would hide 45
	# things that work: a query with no Insights chart still renders its real
	# result rows as a table, still exports, and still drills down to records.
	# Felix's own instruction was that he would rather see everything available
	# than have things silently missing, so the chart-less ones are offered and
	# labelled rather than withheld.
	built = chart_presentation.charts_by_query()
	charts = []
	for row in rows:
		chart = built.get(row["name"]) or {}
		charts.append({
			"chart": row["name"],
			"title": row.get("title") or row["name"],
			"chart_type": chart.get("chart_type") or "",
			"has_chart": bool(chart),
		})
	return {"ok": True, "charts": charts}


def get_tab(criterion, tab):
	"""Everything this tab holds, for one render."""
	criterion, tab = _validated(criterion, tab)
	config = _stored(criterion, tab)
	titles = readable([item["chart"] for item in config["charts"]])
	return {
		"ok": True,
		"criterion": criterion,
		"tab": tab,
		"charts": [
			{"chart": item["chart"], "title": titles[item["chart"]], "span": item["span"]}
			for item in config["charts"] if item["chart"] in titles
		],
		"intro": config["intro"],
		"questions": config["questions"],
		# The page renders the same tab for everyone and shows the edit
		# controls only when this is true. It is a UI signal, not the gate --
		# every write endpoint checks again.
		"can_edit": can_edit(),
		"max": MAX_PER_TAB,
		"columns": GRID_COLUMNS,
	}


def add(criterion, tab, chart):
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	chart = clean_text(chart)
	# Permission BEFORE existence: same reason every other endpoint here does
	# it, so a stranger cannot use the error text to learn which ids exist.
	if not readable([chart]):
		frappe.throw(frappe._("That chart is not available to your account."), frappe.PermissionError)
	config = _stored(criterion, tab)
	if any(item["chart"] == chart for item in config["charts"]):
		return get_tab(criterion, tab)
	if len(config["charts"]) >= MAX_PER_TAB:
		frappe.throw(frappe._("A tab holds at most {0} charts. Remove one first.").format(MAX_PER_TAB))
	config["charts"].append({"chart": chart, "span": DEFAULT_SPAN})
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "chart_added",
		tab_audit.added(readable([chart]).get(chart), chart), after=chart)
	return get_tab(criterion, tab)


def remove(criterion, tab, chart):
	"""Removing needs no permission check on the chart itself: dropping an id
	from your own list is always allowed, and is the only way out if a chart
	you can no longer read is still stored."""
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	chart = clean_text(chart)
	config = _stored(criterion, tab)
	if not any(item["chart"] == chart for item in config["charts"]):
		return get_tab(criterion, tab)
	config["charts"] = [item for item in config["charts"] if item["chart"] != chart]
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "chart_removed",
		tab_audit.removed(readable([chart]).get(chart), chart), before=chart)
	return get_tab(criterion, tab)


def set_size(criterion, tab, chart, span):
	"""Resize one card to a whole number of grid columns.

	The card is dragged, and the drag snaps to the grid before it gets here, so
	this only has to refuse what is off the grid entirely. No permission check
	on the chart itself: a width reveals nothing, and an unreadable chart still
	does not render.
	"""
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	chart = clean_text(chart)
	try:
		span = int(span)
	except (TypeError, ValueError):
		frappe.throw(frappe._("A chart width must be a whole number of columns."), frappe.ValidationError)
	if span < 1 or span > GRID_COLUMNS:
		frappe.throw(
			frappe._("A chart must be between 1 and {0} columns wide.").format(GRID_COLUMNS),
			frappe.ValidationError)
	config = _stored(criterion, tab)
	before = None
	for item in config["charts"]:
		if item["chart"] == chart:
			before = item["span"]
			item["span"] = span
	if before is None or before == span:
		return get_tab(criterion, tab)
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "chart_resized",
		tab_audit.resized(readable([chart]).get(chart), chart, before, span),
		before=before, after=span)
	return get_tab(criterion, tab)


def set_order(criterion, tab, order):
	"""Reorder the cards on a tab. The stored list IS the display order, so
	this rewrites it -- it does not add a second ordering field that could
	disagree with the list.

	Ids not currently on the tab are ignored, and anything the caller left out
	keeps its place at the end. A dropped card would be a silent deletion
	through a reorder endpoint, which is not what a drag means.
	"""
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	if isinstance(order, str):
		try:
			order = json.loads(order)
		except (TypeError, ValueError):
			frappe.throw(frappe._("A chart order must be a list."), frappe.ValidationError)
	if not isinstance(order, list):
		frappe.throw(frappe._("A chart order must be a list."), frappe.ValidationError)

	config = _stored(criterion, tab)
	by_chart = {item["chart"]: item for item in config["charts"]}
	before = [item["chart"] for item in config["charts"]]
	reordered = []
	for chart in order:
		item = by_chart.pop(clean_text(chart), None)
		if item:
			reordered.append(item)
	reordered.extend(item for item in config["charts"] if item["chart"] in by_chart)
	after = [item["chart"] for item in reordered]
	if after == before:
		return get_tab(criterion, tab)
	config["charts"] = reordered
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "charts_reordered",
		tab_audit.reordered(len(after)), before=before, after=after)
	return get_tab(criterion, tab)


def set_intro(criterion, tab, intro):
	"""The tab's own intro text, replacing the hard-coded 'Permission-aware
	live evidence, visual analysis and management questions' every tab used to
	carry. Stored as written; the page renders a small, escaped Markdown subset
	(see askEsc/renderIntro) so this can never become an HTML injection point.
	Empty by default -- no tab is given words nobody chose."""
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	config = _stored(criterion, tab)
	before = config["intro"]
	config["intro"] = clean_text(intro)[:MAX_INTRO_LENGTH]
	if before == config["intro"]:
		return get_tab(criterion, tab)
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "intro_edited",
		tab_audit.intro_edited(before, config["intro"]), before=before, after=config["intro"])
	return get_tab(criterion, tab)


def set_question(criterion, tab, question, visible):
	"""Show or hide one management question on this tab.

	ONE list -- what is hidden -- because the default has to stay "everything
	the criterion engine can answer". Storing what to SHOW instead would have
	emptied the Q&A table on all six criteria that already work, the moment
	this shipped.

	So the two controls are symmetric: the x on a row hides it, and
	"+ Add question" offers exactly the rows currently hidden. The catalogue is
	the criterion's own answerable set, never free text -- the same
	allowlist-not-free-text rule Ask UCC's guided questions follow.

	No answer is stored here, only which question to ask. Every answer is
	computed live and permission-checked on each request, exactly as before.
	"""
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	question = clean_text(question)
	if not question or len(question) > 200:
		frappe.throw(frappe._("Unknown question."), frappe.ValidationError)
	visible = str(visible).lower() not in ("0", "false", "none", "")
	config = _stored(criterion, tab)
	hidden = [q for q in config["questions"]["hidden"] if q != question]
	if not visible:
		if len(hidden) >= MAX_QUESTION_IDS:
			frappe.throw(frappe._("That is as many hidden questions as one tab can carry."))
		hidden.append(question)
	before = list(config["questions"]["hidden"])
	if before == hidden:
		return get_tab(criterion, tab)
	config["questions"] = {"hidden": hidden}
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "question_shown" if visible else "question_hidden",
		tab_audit.question_visibility(question, visible), before=before, after=hidden)
	return get_tab(criterion, tab)


def chart_data(chart, criterion=None, tab=None):
	"""Execute one embedded chart, returning BOTH shapes it is displayed in:
	`series` for the diagram and `columns`/`rows` for the table.

	One execute, two views. The table is the query's own result rows, not a
	second query and not a client-side reconstruction -- so the number in the
	table is by construction the number in the bar.

	Never raises: a chart that fails shows as a failed chart, it does not take
	the tab down with it (CLAUDE.md §14.3). check_permission("read") +
	execute() is the same pair proved on the bench for the admission charts,
	re-checked here at read time rather than inherited from whenever the chart
	was added.
	"""
	chart = clean_text(chart)
	if not chart:
		return {"status": "query_error", "chart": chart, "series": [], "rows": [],
			"columns": [], "message": "No chart given."}
	try:
		doc = frappe.get_doc(CHART_DOCTYPE, chart)
		doc.check_permission("read")
		result = doc.execute(page_size=1000)
	except frappe.PermissionError as error:
		return {"status": "permission_denied", "chart": chart, "series": [], "rows": [],
			"columns": [], "message": clean_text(error)}
	except frappe.DoesNotExistError:
		return {"status": "unavailable", "chart": chart, "series": [], "rows": [], "columns": [],
			"message": "This chart no longer exists in Insights."}
	except Exception as error:
		return {"status": "query_error", "chart": chart, "series": [], "rows": [], "columns": [],
			"message": clean_text(error)}
	rows = result.get("rows") or []
	columns = list(rows[0].keys()) if rows else []
	# How it should LOOK comes from the Insights Chart record built on this
	# query, if there is one and this user may read it. Passing the real
	# columns is what stops a stale config column being rendered against --
	# see chart_presentation.presentation_for().
	presentation = chart_presentation.presentation_for(
		chart, columns=columns, palette=_palette_for(criterion, tab, chart))
	return {
		"status": "available",
		"chart": chart,
		"title": doc.get("title") or chart,
		"series": rows_to_chart_series(rows),
		"columns": columns,
		"rows": rows,
		"presentation": presentation,
	}


def _palette_for(criterion, tab, chart):
	"""This chart's colour override ON THIS TAB, if it has one.

	Scoped to the tab it was asked for rather than searched across every tab.
	That is not only cheaper -- it is more correct, because the same Insights
	chart embedded on two criteria can legitimately want different colours,
	and it avoids a permission-blind sweep of the whole configuration table to
	answer a cosmetic question.
	"""
	if not (criterion and tab):
		return None
	try:
		criterion, tab = _validated(criterion, tab)
	except Exception:
		return None
	for item in _stored(criterion, tab)["charts"]:
		if item.get("chart") == chart:
			return item.get("palette")
	return None


def set_palette(criterion, tab, chart, palette):
	"""Override the series colours for one chart on one tab.

	Same write gate as every other tab change, and audited the same way. An
	empty value clears the override and the chart goes back to the
	institution's default from UCC Intelligence Settings.
	"""
	criterion, tab = _validated(criterion, tab)
	_require_edit()
	chart = clean_text(chart)
	colours = chart_presentation.normalise_palette(palette)
	config = _stored(criterion, tab)
	before = None
	for item in config["charts"]:
		if item.get("chart") != chart:
			continue
		before = item.get("palette")
		if colours:
			item["palette"] = colours
		else:
			item.pop("palette", None)
	if before == (colours or None):
		return get_tab(criterion, tab)
	_store(criterion, tab, config)
	tab_audit.record(criterion, tab, "chart_recoloured",
		"Recoloured the chart %r" % chart, before=before, after=colours)
	return get_tab(criterion, tab)


def history(criterion, tab, limit=50):
	"""The change history for one tab, for the History view.

	Validated the same way every other read is, so the audit trail cannot be
	used to enumerate criteria a user may not see.
	"""
	criterion, tab = _validated(criterion, tab)
	return {"ok": True, "criterion": criterion, "tab": tab,
		"changes": tab_audit.history(criterion, tab, limit)}
