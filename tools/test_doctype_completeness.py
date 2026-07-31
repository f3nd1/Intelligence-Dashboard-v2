#!/usr/bin/env python3
"""Every DocType must be installable. Checked structurally, not one crash
at a time.

WHY THIS EXISTS
`bench migrate` aborted at 38% with:

    ModuleNotFoundError: No module named
    'ucc_intelligence.sophia.doctype.ucc_knowledge_chunk.ucc_knowledge_chunk'

Frappe imports `<module>.doctype.<snake_name>.<snake_name>` for every
DocType it installs. Six DocTypes had a .json and an __init__.py but no
controller module, so migration died on the first one and the eight after it
never installed. Nothing in the offline suite noticed, because nothing was
checking the shape Frappe actually requires.

This checks all of it at once: JSON, __init__.py, controller module, a class
that subclasses Document, and that the class name matches what Frappe will
derive. A missing piece fails here, in a second, instead of half way through
a migration on a live site.

    python3 tools/test_doctype_completeness.py
"""
import ast
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "ucc_intelligence" / "ucc_intelligence"

checks = []


def report(ok, message, detail=""):
	print(("PASS" if ok else "FAIL") + ": " + message + (("\n        " + detail) if detail and not ok else ""))
	checks.append(bool(ok))
	return bool(ok)


def scrub(name):
	"""Frappe's own scrub(): lowercase, spaces and hyphens to underscores."""
	return name.lower().replace(" ", "_").replace("-", "_")


doctype_dirs = sorted(
	d for d in (APP / "sophia" / "doctype").iterdir()
	if d.is_dir() and d.name != "__pycache__"
)
report(len(doctype_dirs) >= 11, "the DocType directory is populated (%d DocTypes)" % len(doctype_dirs))

for directory in doctype_dirs:
	slug = directory.name

	json_path = directory / ("%s.json" % slug)
	if not report(json_path.exists(), "%s: has %s.json" % (slug, slug)):
		continue
	try:
		definition = json.loads(json_path.read_text(encoding="utf-8"))
	except Exception as error:
		report(False, "%s: its JSON parses" % slug, str(error))
		continue

	doctype_name = definition.get("name") or ""
	report(scrub(doctype_name) == slug,
		"%s: the folder name matches scrub(%r) -- Frappe derives the import path from it" % (slug, doctype_name),
		"folder %r but scrub(name) is %r" % (slug, scrub(doctype_name)))

	report((directory / "__init__.py").exists(),
		"%s: has __init__.py, so the folder is an importable package" % slug)

	# THE ONE THAT BROKE MIGRATE.
	controller = directory / ("%s.py" % slug)
	if not report(controller.exists(),
			"%s: has its controller module %s.py -- bench migrate imports this by name" % (slug, slug),
			"missing; bench migrate will raise ModuleNotFoundError and abort"):
		continue

	source = controller.read_text(encoding="utf-8")
	try:
		tree = ast.parse(source)
	except SyntaxError as error:
		report(False, "%s: the controller parses" % slug, str(error))
		continue

	classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
	if not report(classes, "%s: the controller defines a class" % slug):
		continue

	bases = {
		(base.id if isinstance(base, ast.Name) else getattr(base, "attr", ""))
		for cls in classes for base in cls.bases
	}
	report("Document" in bases,
		"%s: its class subclasses Document" % slug,
		"bases found: %s" % sorted(bases))

	# Frappe resolves the class by stripping non-alphanumerics from the
	# DocType name. A mismatch imports fine and then fails at runtime, which
	# is harder to trace than a missing file.
	expected = re.sub(r"[^A-Za-z0-9]", "", doctype_name)
	report(any(cls.name == expected for cls in classes),
		"%s: its class is named %r, which is what Frappe derives from %r" % (slug, expected, doctype_name),
		"found %s" % [cls.name for cls in classes])

	report("from frappe.model.document import Document" in source,
		"%s: imports Document from frappe.model.document" % slug)

# Fixtures reference DocTypes too -- a workflow bound to a DocType that does
# not exist installs and then silently governs nothing.
fixtures_dir = APP / "fixtures"
if fixtures_dir.is_dir():
	known = {json.loads((d / ("%s.json" % d.name)).read_text(encoding="utf-8")).get("name")
		for d in doctype_dirs if (d / ("%s.json" % d.name)).exists()}
	for fixture_path in sorted(fixtures_dir.glob("*.json")):
		try:
			rows = json.loads(fixture_path.read_text(encoding="utf-8"))
		except Exception as error:
			report(False, "fixture %s parses" % fixture_path.name, str(error))
			continue
		report(True, "fixture %s parses" % fixture_path.name)
		for row in rows if isinstance(rows, list) else []:
			target = row.get("document_type")
			if target:
				report(target in known,
					"fixture %s targets %r, which this app defines" % (fixture_path.name, target),
					"known DocTypes: %s" % sorted(known))

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
