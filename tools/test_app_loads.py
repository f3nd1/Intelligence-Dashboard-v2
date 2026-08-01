#!/usr/bin/env python3
"""Can Frappe LOAD this app at all?

    python3 tools/test_app_loads.py

WHY THIS EXISTS
On 2026-08-01 the bench failed with:

    ModuleNotFoundError: No module named 'ucc_intelligence.hooks'

`bench migrate` and `bench clear-cache` both stop there, for every app on the
bench, because Frappe imports `<app>.hooks` before it does anything else.

hooks.py had never been in this repository. It was a recorded decision --
docs/migration/hooks-reference.md said the scaffold is bench-generated and
belongs on the bench -- and the consequence was that this repository's
`ucc_intelligence/` directory did not match the bench's app directory. Any
mirroring sync that deletes extra files at the destination therefore deleted
the app's own manifest. One flag, whole app gone.

Every other suite in this repository checks what the code DOES. None of them
checked that the app could be loaded in the first place, so a missing manifest
was invisible to all of them. This is that check.

WHAT IT COVERS
The files Frappe touches before any of this app's code runs, plus the two
things in them that must agree with the tree: the app name, and the module
list. Nothing here needs a bench -- it is all structure, which is exactly why
it should have been running all along.
"""
import ast
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "ucc_intelligence"
PACKAGE = APP_ROOT / "ucc_intelligence"

checks = []


def report(ok, message, detail=""):
	checks.append(bool(ok))
	print(("PASS" if ok else "FAIL") + ": " + message + (("\n        " + detail) if detail and not ok else ""))
	return bool(ok)


# --- the files Frappe needs before any app code runs ------------------------
# Ordered by when Frappe reaches them, so a failure names the first thing that
# would actually stop a migrate.
REQUIRED = [
	(PACKAGE / "__init__.py", "the app package itself is importable"),
	(PACKAGE / "hooks.py", "frappe.get_hooks() imports <app>.hooks before anything else"),
	(PACKAGE / "modules.txt", "frappe reads the module list to install DocTypes and Pages"),
	(PACKAGE / "patches.txt", "bench migrate reads the patch list on every run"),
	(APP_ROOT / "pyproject.toml", "bench setup requirements and any reinstall need the package metadata"),
]
for path, why in REQUIRED:
	report(path.exists(), "%s exists -- %s" % (path.relative_to(ROOT), why),
		"MISSING. Frappe cannot load the app without it; bench migrate will abort.")

missing = [path for path, _ in REQUIRED if not path.exists()]
if missing:
	print("\nFAIL: %d/%d checks -- stopping, the app cannot load" % (sum(checks), len(checks)))
	sys.exit(1)

# --- hooks.py: parses, and says what it must --------------------------------
hooks_source = (PACKAGE / "hooks.py").read_text(encoding="utf-8")
try:
	hooks = {}
	exec(compile(ast.parse(hooks_source), "hooks.py", "exec"), hooks)  # noqa: S102
	report(True, "hooks.py parses and executes")
except Exception as error:
	report(False, "hooks.py parses and executes", "%s: %s" % (type(error).__name__, error))
	hooks = {}

for attribute in ("app_name", "app_title", "app_publisher", "app_description", "app_email", "app_license"):
	value = hooks.get(attribute)
	report(isinstance(value, str) and value.strip(), "hooks.py declares %s" % attribute,
		"missing or empty -- bench install-app reads all six")

report(hooks.get("app_name") == PACKAGE.name,
	"hooks.app_name matches the package directory (%r)" % PACKAGE.name,
	"app_name is %r but the package is %r -- Frappe resolves modules by app_name"
	% (hooks.get("app_name"), PACKAGE.name))

# hooks.py must not import anything at module scope: frappe imports it very
# early, before the app's own dependencies are guaranteed importable, and a
# stray import there fails the whole bench rather than one feature.
tree = ast.parse(hooks_source)
imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
report(not imports, "hooks.py imports nothing at module scope",
	"imports at module scope: %s" % [ast.unparse(node) for node in imports])

# --- hooks entries must point at code that exists ---------------------------
# A scheduler entry naming a function that is not there fails at 2am in a
# worker log, which is the worst place to find out.
for cadence, handlers in (hooks.get("scheduler_events") or {}).items():
	for handler in handlers:
		module_path, _, function_name = handler.rpartition(".")
		relative = pathlib.Path(*module_path.split(".")[1:]).with_suffix(".py")
		module_file = PACKAGE / relative
		if not report(module_file.exists(), "scheduler %s handler module exists: %s" % (cadence, module_path),
				"no such file: %s" % module_file.relative_to(ROOT)):
			continue
		found = any(
			isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
			for node in ast.parse(module_file.read_text(encoding="utf-8")).body)
		report(found, "scheduler %s handler is defined: %s()" % (cadence, handler),
			"%s has no top-level %s()" % (relative, function_name))

fixture_doctypes = {entry.get("dt") for entry in (hooks.get("fixtures") or []) if isinstance(entry, dict)}
report("Workflow" in fixture_doctypes,
	"hooks.py exports the approval Workflow as a fixture",
	"without it nothing can reach Approved, so no controlled action can execute")
report((PACKAGE / "fixtures" / "workflow.json").exists(),
	"the workflow fixture file the hooks refer to is present")

# --- modules.txt must agree with the tree AND with the DocTypes -------------
modules = [line.strip() for line in (PACKAGE / "modules.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
report(modules, "modules.txt is not empty", "an empty module list installs no DocTypes and no Pages")

declared = set()
for path in PACKAGE.rglob("*.json"):
	if "__pycache__" in str(path):
		continue
	try:
		document = json.loads(path.read_text(encoding="utf-8"))
	except Exception:
		continue
	if isinstance(document, dict) and document.get("module"):
		declared.add(document["module"])

for module in sorted(declared):
	report(module in modules, "module %r used by a DocType/Page is listed in modules.txt" % module,
		"modules.txt has %s -- Frappe will not install records for an unlisted module" % modules)

for module in modules:
	directory = PACKAGE / module.lower().replace(" ", "_").replace("-", "_")
	report(directory.is_dir(), "module %r has its directory (%s)" % (module, directory.name),
		"listed in modules.txt but there is no such directory")

# --- the package declares a version -----------------------------------------
init_source = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
report("__version__" in init_source, "__init__.py declares __version__",
	"pyproject.toml uses dynamic = [\"version\"], which reads it from here")

print(("PASS" if all(checks) else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
sys.exit(0 if all(checks) else 1)
