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

WHERE IT LIVES
`frappe.defaults`, per user, one key per tab (see _key). That is Frappe's own
per-user key/value store -- no new DocType, no migration, no fixture. This app
had no existing server-side per-user config to follow: the only precedent was
localStorage["ucc.dashboard"], which is per browser rather than per user.

Per USER, deliberately and consistently: the tab intro and the question
selection live in the SAME record as the charts, so one person curating a tab
never rearranges anyone else's. That is a real trade-off for the intro text in
particular -- an intro someone writes is only visible to them. Making any of it
institution-wide is the same single change (a shared layer beside this one, see
ADR-014's revisit triggers), and it belongs in one place because everything a
tab holds is in one place.

PERMISSIONS -- THREE GATES, NONE OF THEM THE PICKER'S UI
  1. the criterion tab itself: ucc_dashboard_access must show it to this user
  2. the search: frappe.get_list applies read permission + user permissions,
     so a query the user cannot read is never offered
  3. every read afterwards: get_tab re-filters stored ids through the same list
     call, and chart_data() calls check_permission("read") before executing.
     Access revoked after a chart was added means it stops appearing -- a
     stored id is a preference, never a grant.
"""

import json

import frappe

from ucc_intelligence.analytics.admission_intelligence_embed import clean_text, rows_to_chart_series
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

# frappe.defaults key. Namespaced so it can never collide with a fieldname --
# defaults whose key matches a field are used to prefill new documents.
DEFAULTS_PREFIX = "ucc_sophia_tab_charts"

# A tab is a place to look at a few things, not a dumping ground. Bounded so a
# stored value stays small and a tab stays loadable.
MAX_PER_TAB = 12
MAX_INTRO_LENGTH = 4000
MAX_QUESTION_IDS = 60

# Card widths, as a fraction of the tab's chart grid (12 columns). A picker,
# not drag-resize: four honest choices beat a pixel value nobody can reproduce
# on the next screen size.
SIZES = {"small": 3, "medium": 6, "large": 9, "full": 12}
DEFAULT_SIZE = "medium"

# Tab keys come from the page (criterion sub-sections such as "4.1.1", plus
# "overview"). Constrained so a caller cannot write an arbitrary defaults key.
TAB_CHARACTERS = set("abcdefghijklmnopqrstuvwxyz0123456789._-")


def _key(criterion, tab):
	return "%s:%s:%s" % (DEFAULTS_PREFIX, criterion, tab)


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


def _blank():
	return {"charts": [], "intro": "", "questions": {"hidden": []}}


def _stored(criterion, tab):
	"""The raw stored config. Anything unreadable is treated as absent rather
	than repaired -- a corrupt preference should cost a person their tab
	layout, not raise on every page load.

	Accepts the ORIGINAL shape too: the first version of this stored a bare
	list of chart ids, before sizes, intros and question choices existed. A
	stored list is read as charts at the default size rather than discarded.
	"""
	raw = frappe.defaults.get_user_default(_key(criterion, tab))
	config = _blank()
	if not raw:
		return config
	try:
		stored = json.loads(raw)
	except (TypeError, ValueError):
		return config

	if isinstance(stored, list):
		stored = {"charts": stored}
	if not isinstance(stored, dict):
		return config

	for item in (stored.get("charts") or [])[:MAX_PER_TAB]:
		if isinstance(item, str) and item:
			config["charts"].append({"chart": item, "size": DEFAULT_SIZE})
		elif isinstance(item, dict) and item.get("chart"):
			size = item.get("size")
			config["charts"].append({
				"chart": str(item["chart"]),
				"size": size if size in SIZES else DEFAULT_SIZE,
			})

	intro = stored.get("intro")
	if isinstance(intro, str):
		config["intro"] = intro[:MAX_INTRO_LENGTH]

	questions = stored.get("questions")
	if isinstance(questions, dict) and isinstance(questions.get("hidden"), list):
		config["questions"]["hidden"] = [
			str(v) for v in questions["hidden"] if isinstance(v, str) and v][:MAX_QUESTION_IDS]
	return config


def _store(criterion, tab, config):
	frappe.defaults.set_user_default(_key(criterion, tab), json.dumps({
		"charts": config["charts"][:MAX_PER_TAB],
		"intro": (config.get("intro") or "")[:MAX_INTRO_LENGTH],
		"questions": {"hidden": config["questions"]["hidden"][:MAX_QUESTION_IDS]},
	}))


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
	return {"ok": True, "charts": [
		{"chart": row["name"], "title": row.get("title") or row["name"]} for row in rows]}


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
			{"chart": item["chart"], "title": titles[item["chart"]],
				"size": item["size"], "span": SIZES[item["size"]]}
			for item in config["charts"] if item["chart"] in titles
		],
		"intro": config["intro"],
		"questions": config["questions"],
		"max": MAX_PER_TAB,
		"sizes": sorted(SIZES, key=lambda name: SIZES[name]),
	}


def add(criterion, tab, chart):
	criterion, tab = _validated(criterion, tab)
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
	config["charts"].append({"chart": chart, "size": DEFAULT_SIZE})
	_store(criterion, tab, config)
	return get_tab(criterion, tab)


def remove(criterion, tab, chart):
	"""Removing needs no permission check on the chart itself: dropping an id
	from your own list is always allowed, and is the only way out if a chart
	you can no longer read is still stored."""
	criterion, tab = _validated(criterion, tab)
	chart = clean_text(chart)
	config = _stored(criterion, tab)
	config["charts"] = [item for item in config["charts"] if item["chart"] != chart]
	_store(criterion, tab, config)
	return get_tab(criterion, tab)


def set_size(criterion, tab, chart, size):
	"""Resize one card. No permission check on the chart: this changes a number
	in your own layout and reveals nothing -- an unreadable chart still will
	not render."""
	criterion, tab = _validated(criterion, tab)
	chart = clean_text(chart)
	size = clean_text(size)
	if size not in SIZES:
		frappe.throw(frappe._("Unknown chart size."), frappe.ValidationError)
	config = _stored(criterion, tab)
	for item in config["charts"]:
		if item["chart"] == chart:
			item["size"] = size
	_store(criterion, tab, config)
	return get_tab(criterion, tab)


def set_intro(criterion, tab, intro):
	"""The tab's own intro text, replacing the hard-coded 'Permission-aware
	live evidence, visual analysis and management questions' every tab used to
	carry. Stored as written; the page renders a small, escaped Markdown subset
	(see askEsc/renderIntro) so this can never become an HTML injection point.
	Empty by default -- no tab is given words nobody chose."""
	criterion, tab = _validated(criterion, tab)
	config = _stored(criterion, tab)
	config["intro"] = clean_text(intro)[:MAX_INTRO_LENGTH]
	_store(criterion, tab, config)
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
	config["questions"] = {"hidden": hidden}
	_store(criterion, tab, config)
	return get_tab(criterion, tab)


def chart_data(chart):
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
	return {
		"status": "available",
		"chart": chart,
		"title": doc.get("title") or chart,
		"series": rows_to_chart_series(rows),
		"columns": list(rows[0].keys()) if rows else [],
		"rows": rows,
	}
