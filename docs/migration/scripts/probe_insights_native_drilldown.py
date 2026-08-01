"""What Insights' own DrillDown does, and whether it applies Frappe permissions.

WHY
Section 6 of the Chart v3 probe found `DrillDown.vue...js` among Insights' built
frontend assets. Insights has a native drill-down that nobody on this project
has looked at. Two outcomes are both worth having:

  - it resolves a segment to source rows THROUGH a permission-applying path,
    in which case analytics/drilldown.py may be reinventing it; or
  - it runs raw SQL the way execute() does, in which case it must never replace
    the get_list path, and this probe is the evidence for saying so.

The question is NOT "what does the Vue component look like". It is "which
server endpoint does it call, and what does that endpoint do about
permissions". A component is client-side; permissions are decided on the
server. So this finds the endpoint from the shipped bundle and then reads the
Python it resolves to, on this bench, at this version.

WHAT COUNTS AS PERMISSION-SAFE
  frappe.get_list                 applies read permission, user permissions and
                                  the DocType's permission_query_conditions
  frappe.get_all                  applies NONE of them
  frappe.db.sql / raw ibis        applies none of them
  ignore_permissions=True         explicitly turns them off
  check_permission / has_permission  a gate, but on WHICH doctype matters --
                                  permission on the Query document is not
                                  permission on the records it counted

RUN
    bench --site <site> console
    >>> exec(open("/home/felixoking/Intelligence-Dashboard-v2/docs/migration/scripts/probe_insights_native_drilldown.py").read(), globals())

SAFETY
Read-only. Reads files and Python source. Creates nothing, changes nothing,
executes no query.
"""

import inspect
import os
import re

import frappe

# What we are looking for in the shipped bundles.
ASSET_HINTS = ("drilldown", "drill_down", "usechartdata", "chartrenderer", "basechart")

# A dotted server path as it survives minification, e.g. "insights.api.x.y".
METHOD_PATTERN = re.compile(r"(?:insights|frappe)(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}")
API_PATH_PATTERN = re.compile(r"/api/method/([A-Za-z0-9_.]+)")

# Scanned for in the resolved Python. Order matters only for reading.
SAFE_MARKERS = ("frappe.get_list(", "check_permission(", "has_permission(")
UNSAFE_MARKERS = ("frappe.get_all(", "frappe.db.sql(", "ignore_permissions=True",
	"ignore_permissions = True", ".run(", "raw_sql")


def head(number, title):
	print("\n" + "=" * 72)
	print("%s. %s" % (number, title))
	print("=" * 72)


def insights_path():
	try:
		return frappe.get_app_path("insights")
	except Exception as error:
		print("   the insights app path is unavailable: %s" % error)
		return ""


# --- 1 -----------------------------------------------------------------------

def find_assets(app_path):
	head(1, "THE SHIPPED DRILL-DOWN ASSETS")
	found = []
	for root, _dirs, files in os.walk(app_path):
		if "node_modules" in root:
			continue
		for filename in files:
			if not filename.lower().endswith((".js", ".mjs")):
				continue
			if not any(hint in filename.lower() for hint in ASSET_HINTS):
				continue
			full = os.path.join(root, filename)
			found.append(full)
			print("   %-12s %s" % ("%.1f KB" % (os.path.getsize(full) / 1024.0),
				full.replace(app_path, "").lstrip("/")))
	if not found:
		print("   none matched %s" % (ASSET_HINTS,))
	return found


# --- 2 -----------------------------------------------------------------------

def extract_methods(paths):
	head(2, "WHICH SERVER ENDPOINTS THOSE ASSETS CALL")
	print("   String literals survive minification, so the method paths the")
	print("   component calls are still readable in the built file.\n")
	methods = set()
	for path in paths:
		try:
			with open(path, "r", encoding="utf-8", errors="ignore") as handle:
				text = handle.read()
		except Exception as error:
			print("   could not read %s: %s" % (os.path.basename(path), error))
			continue
		hits = set(METHOD_PATTERN.findall(text)) | set(API_PATH_PATTERN.findall(text))
		if hits:
			print("   --- %s ---" % os.path.basename(path)[:60])
			for hit in sorted(hits):
				print("      %s" % hit)
			methods |= hits
	if not methods:
		print("   no dotted server paths found -- the component may call a")
		print("   generic endpoint (e.g. the same execute() the chart uses)")
	return sorted(methods)


# --- 3 -----------------------------------------------------------------------

def verdict_for(source):
	unsafe = [marker for marker in UNSAFE_MARKERS if marker in source]
	safe = [marker for marker in SAFE_MARKERS if marker in source]
	if unsafe and not safe:
		return "PERMISSION-BLIND -- %s, and no permission-applying call" % ", ".join(unsafe)
	if unsafe and safe:
		return "MIXED -- has %s AND %s; read the code before trusting it" % (
			", ".join(safe), ", ".join(unsafe))
	if safe:
		return "applies permissions via %s -- confirm WHICH doctype" % ", ".join(safe)
	return "no permission markers either way -- read the source below"


def inspect_methods(methods):
	head(3, "WHAT THOSE ENDPOINTS DO ABOUT PERMISSIONS")
	print("   The whole question. A drill-down that returns records without")
	print("   applying read permission turns a summary count into a leak.\n")
	seen = 0
	for path in methods:
		if not path.startswith("insights"):
			continue
		try:
			target = frappe.get_attr(path)
		except Exception:
			continue
		if not callable(target):
			continue
		seen += 1
		whitelisted = bool(getattr(target, "whitelisted", False))
		guest = bool(getattr(target, "allow_guest", False))
		print("   --- %s ---" % path)
		print("      whitelisted: %s   allow_guest: %s" % (whitelisted, guest))
		try:
			source = inspect.getsource(target)
		except Exception as error:
			print("      source unavailable: %s" % error)
			continue
		print("      VERDICT: %s" % verdict_for(source))
		print("      ----- source -----")
		for line in source.splitlines()[:60]:
			print("      %s" % line)
		print()
	if not seen:
		print("   none of the extracted paths resolved to a callable")


# --- 4 -----------------------------------------------------------------------

def scan_python(app_path):
	head(4, "ANYTHING DRILL-SHAPED IN INSIGHTS' PYTHON")
	print("   Independent of the bundle: every def whose name mentions drill,")
	print("   detail or source rows, with the same permission scan.\n")
	pattern = re.compile(r"^\s*def\s+(\w*(?:drill|detail|source_row|underlying|row_detail)\w*)\s*\(",
		re.IGNORECASE | re.MULTILINE)
	hits = 0
	for root, _dirs, files in os.walk(app_path):
		if "node_modules" in root or "/public/" in root:
			continue
		for filename in files:
			if not filename.endswith(".py"):
				continue
			full = os.path.join(root, filename)
			try:
				with open(full, "r", encoding="utf-8", errors="ignore") as handle:
					text = handle.read()
			except Exception:
				continue
			for name in pattern.findall(text):
				hits += 1
				relative = full.replace(app_path, "").lstrip("/")
				start = text.index("def %s" % name)
				body = text[start:start + 1800]
				print("   --- %s in %s ---" % (name, relative))
				print("      whitelisted nearby: %s"
					% ("@frappe.whitelist" in text[max(0, start - 200):start]))
				print("      VERDICT: %s" % verdict_for(body))
				for line in body.splitlines()[:35]:
					print("      %s" % line)
				print()
	if not hits:
		print("   no drill-shaped Python at all -- the drill-down is client-side,")
		print("   which would mean it re-runs the SAME execute() with an extra")
		print("   filter and never fetches source records")


# --- 5 -----------------------------------------------------------------------

def probe_execute_permissions(app_path):
	head(5, "WHAT execute() ITSELF DOES ABOUT PERMISSIONS (the baseline)")
	print("   drilldown.py's whole reason for using get_list is that Insights'")
	print("   execute() applies no Frappe record permissions. Confirming that")
	print("   here, on this version, rather than restating it.\n")
	try:
		doctype_class = frappe.get_attr(
			"insights.insights.doctype.insights_query_v3.insights_query_v3.InsightsQueryv3")
	except Exception as error:
		print("   could not load the query controller: %s" % error)
		return
	for name in ("execute", "fetch_results", "build_query"):
		method = getattr(doctype_class, name, None)
		if not callable(method):
			continue
		try:
			source = inspect.getsource(method)
		except Exception:
			continue
		print("   --- %s ---" % name)
		print("      VERDICT: %s" % verdict_for(source))
		for line in source.splitlines()[:40]:
			print("      %s" % line)
		print()


def run():
	app_path = insights_path()
	if not app_path:
		return
	assets = find_assets(app_path)
	methods = extract_methods(assets)
	inspect_methods(methods)
	scan_python(app_path)
	probe_execute_permissions(app_path)
	head("NEXT", "WHAT TO PASTE BACK")
	print("Sections 2, 3, 4 and 5. Section 2 says what the component calls,")
	print("3 and 4 say whether that path applies permissions, and 5 confirms")
	print("the baseline the current design was built against.")


run()
