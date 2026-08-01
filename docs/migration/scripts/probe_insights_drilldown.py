"""Ask the installed Frappe Insights what it can actually do about drill-down,
before anything here re-implements it.

WHY THIS EXISTS RATHER THAN A FEATURE
The Table view beside each embedded chart already shows the query's own result
rows, from the same single execute() the diagram used. Clicking a bar filters
that table to the clicked segment.

What it does NOT do is expand "Consultative · 40" into the 40 underlying
records, because an Insights Query v3's execute() returns the SUMMARISED rows
-- one row per dimension value. Getting the 40 needs a second query against the
source table with the dimension filtered, and the honest question is whether
Insights already offers that.

Writing that second query from memory is exactly the mistake that produced 13
TableNotFound errors earlier in this migration: the operations shape was
written from recollection instead of copied from a version proven on a bench.
So this prints what Insights exposes, and the drill-down is built from what it
finds.

RUN
    bench --site <site> console
    >>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/probe_insights_drilldown.py").read(), globals())

SAFETY
Read-only. Creates nothing, changes nothing, executes one existing query.
"""

import inspect

import frappe

QUERY_DOCTYPE = "Insights Query v3"

# Names worth checking for on the document class. A hit does not mean "use it"
# -- it means "read its signature before writing anything".
INTERESTING = (
	"drill", "detail", "records", "rows", "source", "expand", "underlying",
	"get_rows", "fetch", "results", "preview", "execute",
)


def probe_doctype():
	print("=" * 72)
	print("1. WHAT EXISTS")
	print("=" * 72)
	for doctype in (QUERY_DOCTYPE, "Insights Chart v3", "Insights Dashboard v3", "Insights Data Source v3"):
		print("   %-28s %s" % (doctype, "present" if frappe.db.exists("DocType", doctype) else "ABSENT"))
	if not frappe.db.exists("DocType", QUERY_DOCTYPE):
		print("\nSTOP -- Insights v3 is not installed on this site.")
		return None
	name = frappe.db.get_value(QUERY_DOCTYPE, {}, "name", order_by="modified desc")
	if not name:
		print("\nSTOP -- no %s records exist yet. Build one first." % QUERY_DOCTYPE)
		return None
	print("\n   probing with the most recently modified query: %s" % name)
	return frappe.get_doc(QUERY_DOCTYPE, name)


def probe_methods(doc):
	print("\n" + "=" * 72)
	print("2. METHODS ON THE QUERY DOCUMENT THAT MIGHT ANSWER 'SHOW ME THE ROWS'")
	print("=" * 72)
	found = []
	for attribute in sorted(dir(doc)):
		if attribute.startswith("_"):
			continue
		if not any(word in attribute.lower() for word in INTERESTING):
			continue
		try:
			value = getattr(doc, attribute)
		except Exception:
			continue
		if not callable(value):
			continue
		try:
			signature = str(inspect.signature(value))
		except (TypeError, ValueError):
			signature = "(signature unavailable)"
		found.append(attribute)
		print("   %-32s %s" % (attribute, signature))
		doc_text = (inspect.getdoc(value) or "").strip().splitlines()
		if doc_text:
			print("        %s" % doc_text[0][:110])
	if not found:
		print("   none -- nothing on the document looks like a row/detail accessor")
	return found


def probe_whitelisted():
	print("\n" + "=" * 72)
	print("3. WHITELISTED INSIGHTS ENDPOINTS (what the Insights UI itself calls)")
	print("=" * 72)
	print("   Anything listed here can be called from our own server code. An")
	print("   endpoint that returns SOURCE rows for a dimension value is the one")
	print("   worth having -- if it exists, the drill-down uses it rather than")
	print("   building a query by hand.")
	try:
		import insights  # noqa: F401
	except ImportError:
		print("   the `insights` app is not importable in this context")
		return
	import pkgutil
	import importlib
	shown = 0
	for module_info in pkgutil.walk_packages(__import__("insights").__path__, "insights."):
		if ".api" not in module_info.name and not module_info.name.endswith("api"):
			continue
		try:
			module = importlib.import_module(module_info.name)
		except Exception:
			continue
		for attribute in sorted(dir(module)):
			function = getattr(module, attribute, None)
			if not callable(function) or not getattr(function, "__name__", "").strip("_"):
				continue
			if not getattr(function, "whitelisted", False):
				continue
			if not any(word in attribute.lower() for word in INTERESTING):
				continue
			try:
				signature = str(inspect.signature(function))
			except (TypeError, ValueError):
				signature = "(signature unavailable)"
			print("   %s.%s%s" % (module_info.name, attribute, signature))
			shown += 1
	if not shown:
		print("   none matched -- no whitelisted Insights endpoint looks like a drill-down")


def probe_result_shape(doc):
	print("\n" + "=" * 72)
	print("4. WHAT execute() ACTUALLY RETURNS")
	print("=" * 72)
	print("   This is the shape the Table view already renders. If the rows are")
	print("   one-per-dimension-value, drill-down needs a second query; if they")
	print("   are the source records, it does not.")
	try:
		doc.check_permission("read")
		result = doc.execute(page_size=5)
	except Exception as error:
		print("   execute() failed: %s: %s" % (type(error).__name__, error))
		return
	print("   top-level keys: %s" % sorted(result.keys()))
	rows = result.get("rows") or []
	print("   row count (page_size=5): %d" % len(rows))
	if rows:
		print("   columns: %s" % list(rows[0].keys()))
		print("   first row: %s" % rows[0])
	print("\n   VERDICT: %s" % (
		"summarised -- one row per group, so drill-down needs source rows from somewhere else"
		if rows and len(rows[0]) <= 3
		else "wide/record-like -- check whether these ARE the underlying records"))


def probe_operations(doc):
	print("\n" + "=" * 72)
	print("5. THE QUERY'S OWN OPERATIONS")
	print("=" * 72)
	print("   If a drill-down is built by hand, it is built by copying THIS and")
	print("   removing the summarize step -- not by writing a new one from")
	print("   memory. Copy the printed structure verbatim into the builder.")
	operations = doc.get("operations")
	print("   %s" % frappe.as_json(operations)[:2000])


def run():
	doc = probe_doctype()
	if not doc:
		return
	probe_methods(doc)
	probe_whitelisted()
	probe_result_shape(doc)
	probe_operations(doc)
	print("\n" + "=" * 72)
	print("NEXT")
	print("=" * 72)
	print("Paste sections 2-5 back. If Insights exposes a source-row endpoint,")
	print("the drill-down calls it. If it does not, section 5's operations are")
	print("the proven starting point for a hand-built source query -- copied,")
	print("not recalled.")


run()
