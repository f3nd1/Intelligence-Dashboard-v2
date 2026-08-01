"""Ask the installed Frappe Insights what it can actually do about drill-down,
before anything here re-implements it.

WHY THIS EXISTS RATHER THAN A FEATURE
The Table view beside each embedded chart already shows the query's own result
rows, from the same single execute() the diagram used. Clicking a bar filters
that table to the clicked segment.

What it does NOT do is expand "Consultative · 40" into the 40 underlying
records, because a summarised query returns one row per dimension value.
Getting the 40 needs a second query against the source table with the dimension
filtered, and the honest question is whether Insights already offers that.

Writing that second query from memory is exactly the mistake that produced 13
TableNotFound errors earlier in this migration: the operations shape was
written from recollection instead of copied from a version proven on a bench.
So this prints what Insights exposes, and the drill-down is built from that.

WHAT CHANGED ON 2026-08-01 (second revision)
The first revision probed "the most recently modified query", which turned out
to be an abandoned record with no operations and a failing execute(). It proved
nothing. Two fixes:

  1. It now targets a query that MATTERS -- one actually on a Sophia tab -- and
     accepts an explicit override. A query with an empty operations list is
     never chosen silently; it is reported as unusable and skipped.

  2. It settles the v2-versus-v3 question live (section 1) instead of assuming
     either. Both schemas can be installed at once, and which one a given chart
     belongs to decides every field name a drill-down would use.

RUN -- pick the query yourself (preferred)
    bench --site <site> console
    >>> UCC_PROBE_QUERY = "Stakeholder engagement by status"
    >>> exec(open("/home/felixoking/Intelligence-Dashboard-v2/docs/migration/scripts/probe_insights_drilldown.py").read(), globals())

The value matches on record name OR title, case-insensitively, as a fragment.

RUN -- let it choose
    bench --site <site> console
    >>> exec(open("/home/felixoking/Intelligence-Dashboard-v2/docs/migration/scripts/probe_insights_drilldown.py").read(), globals())

With no override it takes the first chart on a Sophia tab that has operations
and executes, and says which it took and why.

SAFETY
Read-only. Creates nothing, changes nothing, executes existing queries with a
5-row page size.
"""

import inspect
import json

import frappe

# The two schemas, in the order Insights shipped them. A site can carry both:
# v3 was introduced alongside v2 and v2 records survive migration, so "the
# DocType exists" and "this is the live path" are different questions.
V2_DOCTYPES = ("Insights Query", "Insights Chart", "Insights Dashboard",
	"Insights Data Source", "Insights Table")
V3_DOCTYPES = ("Insights Query v3", "Insights Chart v3", "Insights Dashboard v3",
	"Insights Data Source v3", "Insights Table v3", "Insights Workbook")

# Fields that only one schema has. Which of these a record answers to is the
# definitive test for which schema that record belongs to.
V2_MARKER_FIELDS = ("sql", "chart_type", "options", "is_native_query", "data_source")
V3_MARKER_FIELDS = ("operations", "is_builder_query", "use_live_connection", "workbook")

TAB_DOCTYPE = "UCC Analytics Tab"

# Names worth checking for on the document class. A hit does not mean "use it"
# -- it means "read its signature before writing anything".
INTERESTING = (
	"drill", "detail", "records", "rows", "source", "expand", "underlying",
	"get_rows", "fetch", "results", "preview", "execute",
)


def head(number, title):
	print("\n" + "=" * 72)
	print("%s. %s" % (number, title))
	print("=" * 72)


def count(doctype):
	try:
		return frappe.db.count(doctype)
	except Exception as error:
		return "count failed: %s" % error


# --- 1. which schema is real here -------------------------------------------

def probe_schema():
	head(1, "WHICH INSIGHTS SCHEMA IS ACTUALLY IN USE (v2 vs v3)")
	print("   Both can be installed at once. What settles it is not which")
	print("   DocTypes exist but which ones hold the records being used.\n")

	try:
		version = frappe.get_attr("insights.__version__")
	except Exception:
		version = "unknown"
	print("   insights app version: %s" % version)
	print("   installed apps: %s" % ", ".join(frappe.get_installed_apps()))

	present = {}
	for label, doctypes in (("v2", V2_DOCTYPES), ("v3", V3_DOCTYPES)):
		print("\n   --- %s ---" % label)
		for doctype in doctypes:
			if not frappe.db.exists("DocType", doctype):
				print("   %-28s ABSENT" % doctype)
				continue
			rows = count(doctype)
			present[doctype] = rows
			print("   %-28s present, %s record(s)" % (doctype, rows))

	# The question that actually matters: the charts on Felix's tabs -- which
	# schema do THEY live in? Read the real configuration, not an assumption.
	head("1b", "WHAT THE SOPHIA TABS ARE ACTUALLY POINTING AT")
	chart_ids = sophia_chart_ids()
	if not chart_ids:
		print("   no charts are configured on any Sophia tab yet")
		return present, []
	print("   %d chart id(s) configured across all tabs\n" % len(chart_ids))
	resolved = []
	for chart_id in chart_ids:
		homes = [doctype for doctype in present
			if frappe.db.exists(doctype, chart_id)]
		title = ""
		for doctype in homes:
			title = frappe.db.get_value(doctype, chart_id, "title") or ""
			if title:
				break
		print("   %-24s %-40s -> %s" % (
			chart_id, (title or "(no title)")[:40],
			", ".join(homes) if homes else "NOT FOUND IN ANY INSIGHTS DOCTYPE"))
		for doctype in homes:
			resolved.append((doctype, chart_id, title))

	homes = sorted({doctype for doctype, _, _ in resolved})
	print("\n   VERDICT: the Sophia tab charts live in: %s" % (
		", ".join(homes) if homes else "nothing -- none of them resolved"))
	if len(homes) > 1:
		print("   NOTE: more than one schema is in play. Every drill-down field")
		print("         name must be chosen per chart, not once for all of them.")
	return present, resolved


def sophia_chart_ids():
	"""Every chart id configured on a Sophia tab, in tab order."""
	if not frappe.db.exists("DocType", TAB_DOCTYPE):
		return []
	ids = []
	for row in frappe.get_all(TAB_DOCTYPE, fields=["name", "charts"]):
		try:
			for item in json.loads(row.get("charts") or "[]"):
				chart = item.get("chart") if isinstance(item, dict) else item
				if chart and chart not in ids:
					ids.append(chart)
		except Exception:
			continue
	return ids


# --- 2. choose something worth probing --------------------------------------

def describe_shape(doc):
	"""Which schema THIS record answers to, by the fields it actually has."""
	v2 = [field for field in V2_MARKER_FIELDS if doc.get(field) not in (None, "")]
	v3 = [field for field in V3_MARKER_FIELDS if doc.get(field) not in (None, "")]
	return v2, v3


def usable(doc):
	"""A query worth probing has operations (v3) or SQL (v2). Empty is useless."""
	operations = doc.get("operations")
	if isinstance(operations, str):
		try:
			operations = json.loads(operations or "[]")
		except Exception:
			operations = []
	return bool(operations) or bool(doc.get("sql"))


def pick_query(resolved):
	head(2, "WHICH QUERY IS BEING PROBED, AND WHY")
	override = str(globals().get("UCC_PROBE_QUERY") or "").strip()

	candidates = []          # (doctype, name, title, why)
	if override:
		print("   override set: %r" % override)
		needle = override.lower()
		for doctype in V3_DOCTYPES + V2_DOCTYPES:
			if not frappe.db.exists("DocType", doctype):
				continue
			try:
				rows = frappe.get_all(doctype, fields=["name", "title"], limit_page_length=0)
			except Exception:
				continue
			for row in rows:
				if needle in (row.get("name") or "").lower() \
						or needle in (row.get("title") or "").lower():
					candidates.append((doctype, row["name"], row.get("title") or "", "matched the override"))
		if not candidates:
			print("   NOTHING MATCHED %r -- check the title, or run with no override" % override)
			return None
	else:
		print("   no override -- taking charts from the Sophia tabs, in order")
		candidates = [(doctype, name, title, "on a Sophia tab")
			for doctype, name, title in resolved]
		if not candidates:
			print("   no tab charts to fall back on; taking recently modified queries")
			for doctype in V3_DOCTYPES[:1] + V2_DOCTYPES[:1]:
				if not frappe.db.exists("DocType", doctype):
					continue
				for row in frappe.get_all(doctype, fields=["name", "title"],
						order_by="modified desc", limit_page_length=10):
					candidates.append((doctype, row["name"], row.get("title") or "",
						"recently modified"))

	print("\n   %d candidate(s). Taking the first with real content that executes:\n"
		% len(candidates))
	for doctype, name, title, why in candidates:
		try:
			doc = frappe.get_doc(doctype, name)
		except Exception as error:
			print("   SKIP  %-22s %-34s cannot load: %s" % (name, title[:34], error))
			continue
		if not usable(doc):
			print("   SKIP  %-22s %-34s no operations and no SQL -- an empty record"
				% (name, title[:34]))
			continue
		try:
			doc.check_permission("read")
		except Exception as error:
			print("   SKIP  %-22s %-34s not readable: %s" % (name, title[:34], error))
			continue
		try:
			doc.execute(page_size=5)
		except Exception as error:
			print("   SKIP  %-22s %-34s execute() failed: %s"
				% (name, title[:34], str(error)[:60]))
			continue
		v2, v3 = describe_shape(doc)
		print("\n   TAKING %s  (%s, %s)" % (name, doctype, why))
		print("     title:       %s" % (title or "(none)"))
		print("     v2 fields set: %s" % (", ".join(v2) or "none"))
		print("     v3 fields set: %s" % (", ".join(v3) or "none"))
		print("     -> this record is %s" % (
			"v3" if v3 and not v2 else "v2" if v2 and not v3
			else "AMBIGUOUS -- it answers to both, read the values before trusting either"))
		return doc

	print("\n   NONE of the candidates were usable. Nothing here can inform a")
	print("   drill-down design. Name a working chart with UCC_PROBE_QUERY.")
	return None


# --- 3-6. the original probes, unchanged in intent --------------------------

def probe_methods(doc):
	head(3, "METHODS ON THE QUERY DOCUMENT THAT MIGHT ANSWER 'SHOW ME THE ROWS'")
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
	head(4, "WHITELISTED INSIGHTS ENDPOINTS (what the Insights UI itself calls)")
	print("   Anything listed here can be called from our own server code. An")
	print("   endpoint that returns SOURCE rows for a dimension value is the one")
	print("   worth having -- if it exists, the drill-down uses it rather than")
	print("   building a query by hand.")
	try:
		import insights  # noqa: F401
	except ImportError:
		print("   the `insights` app is not importable in this context")
		return
	import importlib
	import pkgutil
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
	head(5, "WHAT execute() ACTUALLY RETURNS")
	print("   This is the shape the Table view already renders. If the rows are")
	print("   one-per-dimension-value, drill-down needs a second query; if they")
	print("   are the source records, it does not.")
	try:
		doc.check_permission("read")
		result = doc.execute(page_size=5)
	except Exception as error:
		print("   execute() failed: %s: %s" % (type(error).__name__, error))
		return
	if not isinstance(result, dict):
		print("   returned a %s, not a dict: %r" % (type(result).__name__, str(result)[:300]))
		return
	print("   top-level keys: %s" % sorted(result.keys()))
	rows = result.get("rows") or []
	print("   row count (page_size=5): %d" % len(rows))
	if rows:
		print("   columns: %s" % list(rows[0].keys()))
		for row in rows[:3]:
			print("   row: %s" % row)
	print("\n   VERDICT: %s" % (
		"summarised -- one row per group, so drill-down needs source rows from somewhere else"
		if rows and len(rows[0]) <= 3
		else "wide/record-like -- check whether these ARE the underlying records"))


def probe_operations(doc):
	head(6, "THE QUERY'S OWN OPERATIONS -- THE THING A DRILL-DOWN COPIES")
	print("   If a drill-down is built by hand, it is built by copying THIS and")
	print("   removing the summarize step -- not by writing a new one from")
	print("   memory. Copy the printed structure verbatim into the builder.\n")
	operations = doc.get("operations")
	if isinstance(operations, str):
		try:
			operations = json.loads(operations or "[]")
		except Exception:
			pass
	print("   %s" % frappe.as_json(operations)[:3000])

	if doc.get("sql"):
		print("\n   this record also has SQL (a v2 marker):")
		print("   %s" % str(doc.get("sql"))[:1500])

	# The two things a source query needs, pulled out by name so they are not
	# hunted for in the JSON above.
	print("\n   --- the fields a drill-down needs, extracted ---")
	print("   use_live_connection: %r" % doc.get("use_live_connection"))
	print("   is_builder_query:    %r" % doc.get("is_builder_query"))
	print("   data_source:         %r" % doc.get("data_source"))
	try:
		for step in (operations or []):
			if not isinstance(step, dict):
				continue
			if step.get("type") == "source":
				print("   SOURCE step:      %s" % frappe.as_json(step)[:600])
			if step.get("type") in ("summarize", "group_by"):
				print("   SUMMARIZE step:   %s" % frappe.as_json(step)[:600])
	except Exception as error:
		print("   could not walk the operations: %s" % error)


def run():
	present, resolved = probe_schema()
	doc = pick_query(resolved)
	probe_whitelisted()
	if not doc:
		print("\nSTOP -- no usable query, so sections 3, 5 and 6 have nothing to")
		print("report. Re-run naming a chart you use, e.g.")
		print('    UCC_PROBE_QUERY = "Stakeholder engagement by status"')
		return
	probe_methods(doc)
	probe_result_shape(doc)
	probe_operations(doc)
	head("NEXT", "WHAT TO PASTE BACK")
	print("Sections 1, 1b, 2, 5 and 6. Section 1 settles v2-vs-v3, section 2")
	print("says which chart the rest describes, and 5 and 6 are the shapes a")
	print("drill-down gets copied from. Sections 3 and 4 are already known.")


run()
