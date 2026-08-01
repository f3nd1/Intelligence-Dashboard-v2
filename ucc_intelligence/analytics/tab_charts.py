# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt
"""Per-tab Insights charts: what a person has chosen to see on one tab.

WHY THIS REPLACED THE OLD CHART BOXES
The dashboard used to ship 222 fixed chart boxes across the seven criteria,
each hard-coded in the page's own LIVE_VISUAL_EXPANSION table and looked up in
a 113-entry registry. Only 16 of them ever had a real Insights query behind
them; the other 206 were blank. Boxes nobody chose, mostly showing nothing.

Now a tab starts with no charts and one "+ Add chart" button. A person picks a
real Insights query -- one they can already read -- and it is embedded on that
tab, for them, until they remove it. Nothing is pre-declared, so nothing can be
declared and then not exist.

WHERE THE SELECTION LIVES
`frappe.defaults`, per user, one key per tab (see _key). That is Frappe's own
per-user key/value store -- no new DocType, no migration, no fixture. This app
had no existing server-side per-user config to follow: the only precedent was
localStorage["ucc.dashboard"], which is per browser rather than per user and
would not survive someone moving desks.

Per USER, deliberately: one person curating their tab must not rearrange
everyone else's. If UCC later wants a shared default layout, it belongs beside
this rather than instead of it, and this module is the only thing that would
change -- every caller goes through get_charts/add/remove.

PERMISSIONS -- THREE GATES, NONE OF THEM THE PICKER'S UI
  1. the criterion tab itself: ucc_dashboard_access must show it to this user
  2. the search: frappe.get_list applies read permission + user permissions,
     so a query the user cannot read is never offered
  3. every read afterwards: get_charts re-filters stored ids through the same
     list call, and chart_data() calls check_permission("read") before
     executing. Access revoked after a chart was added means it stops
     appearing -- a stored id is a preference, never a grant.
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


def _stored(criterion, tab):
	"""The raw stored ids. Anything that is not a list of strings is treated as
	absent rather than repaired -- a corrupt preference should cost a person
	their chart layout, not raise on every page load."""
	raw = frappe.defaults.get_user_default(_key(criterion, tab))
	if not raw:
		return []
	try:
		names = json.loads(raw)
	except (TypeError, ValueError):
		return []
	if not isinstance(names, list):
		return []
	return [name for name in names if isinstance(name, str) and name][:MAX_PER_TAB]


def _store(criterion, tab, names):
	frappe.defaults.set_user_default(_key(criterion, tab), json.dumps(names[:MAX_PER_TAB]))


def readable(names):
	"""Of these chart ids, the ones this user may read, in the order given.

	frappe.get_list -- not get_all -- so permissions and user permissions both
	apply. This is what makes a stored id a preference rather than a grant.
	"""
	if not names:
		return []
	rows = frappe.get_list(
		CHART_DOCTYPE, filters={"name": ["in", names]}, fields=["name", "title"],
		limit_page_length=len(names))
	titles = {row["name"]: row.get("title") or row["name"] for row in rows}
	return [{"chart": name, "title": titles[name]} for name in names if name in titles]


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


def get_charts(criterion, tab):
	criterion, tab = _validated(criterion, tab)
	charts = readable(_stored(criterion, tab))
	return {"ok": True, "criterion": criterion, "tab": tab, "charts": charts,
		"max": MAX_PER_TAB}


def add(criterion, tab, chart):
	criterion, tab = _validated(criterion, tab)
	chart = clean_text(chart)
	# Permission BEFORE existence: same reason every other endpoint here does
	# it, so a stranger cannot use the error text to learn which ids exist.
	if not readable([chart]):
		frappe.throw(frappe._("That chart is not available to your account."), frappe.PermissionError)
	names = _stored(criterion, tab)
	if chart in names:
		return get_charts(criterion, tab)
	if len(names) >= MAX_PER_TAB:
		frappe.throw(frappe._("A tab holds at most {0} charts. Remove one first.").format(MAX_PER_TAB))
	names.append(chart)
	_store(criterion, tab, names)
	return get_charts(criterion, tab)


def remove(criterion, tab, chart):
	"""Removing needs no permission check on the chart itself: dropping an id
	from your own list is always allowed, and is the only way out if a chart
	you can no longer read is still stored."""
	criterion, tab = _validated(criterion, tab)
	chart = clean_text(chart)
	names = [name for name in _stored(criterion, tab) if name != chart]
	_store(criterion, tab, names)
	return get_charts(criterion, tab)


def chart_data(chart):
	"""Execute one embedded chart. Never raises -- a chart that fails shows as
	a failed chart, it does not take the tab down with it (CLAUDE.md §14.3).

	check_permission("read") + execute() is the same pair proved on the bench
	for the admission charts. It is re-checked here, at read time, and not
	inherited from whatever was true when the chart was added.
	"""
	chart = clean_text(chart)
	if not chart:
		return {"status": "query_error", "chart": chart, "series": [], "message": "No chart given."}
	try:
		doc = frappe.get_doc(CHART_DOCTYPE, chart)
		doc.check_permission("read")
		result = doc.execute(page_size=1000)
	except frappe.PermissionError as error:
		return {"status": "permission_denied", "chart": chart, "series": [], "message": clean_text(error)}
	except frappe.DoesNotExistError:
		return {"status": "unavailable", "chart": chart, "series": [],
			"message": "This chart no longer exists in Insights."}
	except Exception as error:
		return {"status": "query_error", "chart": chart, "series": [], "message": clean_text(error)}
	return {
		"status": "available",
		"chart": chart,
		"title": doc.get("title") or chart,
		"series": rows_to_chart_series(result.get("rows") or []),
	}
