"""CLAUDE.md Phase 13 acceptance test: prove the app stands alone.

THE BAR: with every legacy Server Script DISABLED, the whole system must
work unchanged. Felix disabled them on the bench and the system stopped
working -- that is what proved the cutover had never happened. Code review
cannot settle this; only running it with them off can.

WHAT IT DOES
  1. Records the current enabled/disabled state of every UCC Server Script.
  2. Calls every app endpoint WITH the Server Scripts still enabled, and
     keeps the responses as a baseline.
  3. DISABLES every UCC Server Script.
  4. Calls every endpoint again and compares against the baseline.
  5. RE-ENABLES exactly the scripts that were enabled in step 1 -- in a
     `finally`, so a crash mid-run still restores them.
  6. Prints one PASS/FAIL per check and one overall verdict.

Comparison ignores fields that legitimately differ between two runs
(timestamps, generated ids, latency). Everything else must match: if a
response changes when the Server Scripts go away, something was still
reaching them.

RUN
    bench --site <site> console
    >>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/verify_cutover.py").read(), globals())

  The `globals()` argument matters -- without it the top-level defs land in
  locals and cross-function calls raise NameError.

SAFETY
  It disables Server Scripts on a live site for the duration of the run.
  Run it on staging first. It restores state in a `finally` block, and
  prints the restored state at the end so you can confirm. If the process
  is killed between step 3 and step 5, re-enable manually:
      for name in frappe.get_all("Server Script", pluck="name"):
          ...  # the script prints the exact list it disabled
"""

import copy
import json

import frappe

# Response keys that differ between any two runs and say nothing about
# whether the Server Scripts were involved.
VOLATILE_KEYS = {
	"generated_at", "timestamp", "duration_ms", "latency_ms", "elapsed",
	"conversation_id", "diagnostic_id", "request_id", "name", "modified",
	"creation", "last_indexed_at", "started_at", "finished_at",
}

CRITERIA = ["1", "2", "3", "4", "5", "6", "7"]
ASK_MODULES = ["quality_action", "recruitment_agent", "student_journey"]

results = []


def check(ok, message, detail=""):
	results.append((bool(ok), message, detail))
	print("%s %s%s" % ("PASS" if ok else "FAIL", message, ("  -- " + detail) if detail and not ok else ""))
	return bool(ok)


def strip_volatile(value):
	"""A comparable copy: volatile keys removed at every depth."""
	if isinstance(value, dict):
		return {k: strip_volatile(v) for k, v in sorted(value.items()) if k not in VOLATILE_KEYS}
	if isinstance(value, list):
		return [strip_volatile(v) for v in value]
	return value


def comparable(value):
	return json.dumps(strip_volatile(value), sort_keys=True, default=str)


# ---------------------------------------------------------------------------
# Exercising the app. Every call goes through the WHITELISTED method, the
# same entry point the browser uses -- not the internal module -- because
# the whole question is whether the frontend's path still works.
# ---------------------------------------------------------------------------
def call_criterion(number, subcriterion=None):
	from ucc_intelligence import api
	payload = {"action": "summary", "page_size": 50}
	if subcriterion:
		payload["subcriterion"] = subcriterion
	frappe.form_dict["payload"] = json.dumps(payload)
	try:
		return getattr(api, "get_criterion_%s" % number)()
	finally:
		frappe.form_dict.pop("payload", None)


def exercise_everything(label):
	"""One full sweep of every user-facing surface. Returns a dict of
	responses keyed by what was called."""
	from ucc_intelligence import api
	snapshot = {}

	for number in CRITERIA:
		try:
			snapshot["criterion_%s" % number] = call_criterion(number)
		except Exception as error:
			snapshot["criterion_%s" % number] = {"__exception__": "%s: %s" % (type(error).__name__, error)}

	try:
		snapshot["dashboard_access"] = api.get_dashboard_access()
	except Exception as error:
		snapshot["dashboard_access"] = {"__exception__": "%s: %s" % (type(error).__name__, error)}

	try:
		snapshot["ask_modules"] = api.get_ask_ucc_modules()
	except Exception as error:
		snapshot["ask_modules"] = {"__exception__": "%s: %s" % (type(error).__name__, error)}

	for module_key in ASK_MODULES:
		try:
			snapshot["search_%s" % module_key] = api.search_ask_ucc_records(module_key, "a")
		except Exception as error:
			snapshot["search_%s" % module_key] = {"__exception__": "%s: %s" % (type(error).__name__, error)}

	for module_key, record in ASK_RECORDS.items():
		key = "ask_%s" % module_key
		if not record:
			snapshot[key] = {"__skipped__": "no readable record for this module"}
			continue
		try:
			snapshot[key] = api.ask_ucc(module_key, "Show this record", record)
		except Exception as error:
			snapshot[key] = {"__exception__": "%s: %s" % (type(error).__name__, error)}

	try:
		snapshot["admission_intelligence"] = api.get_admission_intelligence()
	except Exception as error:
		snapshot["admission_intelligence"] = {"__exception__": "%s: %s" % (type(error).__name__, error)}

	print("  [%s] exercised %d surfaces" % (label, len(snapshot)))
	return snapshot


def pick_ask_records():
	"""One readable record per Ask UCC module, so the ask path is exercised
	with real data rather than skipped."""
	from ucc_intelligence.ai import orchestration
	chosen = {}
	for module_key, config in orchestration.MODULES.items():
		try:
			names = frappe.get_all(config["doctype"], pluck="name", limit=1)
			chosen[module_key] = names[0] if names else None
		except Exception:
			chosen[module_key] = None
	return chosen


# ---------------------------------------------------------------------------
# Server Script control
# ---------------------------------------------------------------------------
def ucc_server_scripts():
	"""Every Server Script this product ever installed. Matched on the name
	prefix the legacy deployment used."""
	rows = frappe.get_all("Server Script", fields=["name", "disabled"], limit_page_length=0)
	return [r for r in rows if str(r["name"]).lower().startswith("ucc")]


def set_disabled(names, disabled):
	for name in names:
		frappe.db.set_value("Server Script", name, "disabled", 1 if disabled else 0)
	frappe.db.commit()
	frappe.clear_cache()


def run():
	global ASK_RECORDS

	print("=" * 72)
	print("PHASE 13 CUTOVER ACCEPTANCE TEST")
	print("=" * 72)

	scripts = ucc_server_scripts()
	if not scripts:
		print("\nNo UCC Server Scripts found on this site.")
		print("That is the END STATE this test exists to prove, but it also means")
		print("this run cannot demonstrate the transition. Exercising the app anyway.")
	else:
		print("\nFound %d UCC Server Script(s):" % len(scripts))
		for row in scripts:
			print("   %-50s disabled=%s" % (row["name"], row["disabled"]))

	was_enabled = [r["name"] for r in scripts if not r["disabled"]]
	print("\nCurrently ENABLED and will be restored at the end: %s" % (was_enabled or "none"))

	ASK_RECORDS = pick_ask_records()
	print("Ask UCC test records: %s" % ASK_RECORDS)

	try:
		print("\n--- Phase 1: baseline, Server Scripts AS THEY ARE ---")
		baseline = exercise_everything("baseline")

		if was_enabled:
			print("\n--- Phase 2: DISABLING all UCC Server Scripts ---")
			set_disabled(was_enabled, True)
			still_on = [r["name"] for r in ucc_server_scripts() if not r["disabled"]]
			check(not still_on, "every UCC Server Script is now disabled", "still enabled: %s" % still_on)
		else:
			print("\n--- Phase 2: nothing to disable (all already off) ---")

		print("\n--- Phase 3: the real test, app alone ---")
		without = exercise_everything("scripts-off")

		print("\n--- Phase 4: results ---")
		for key in sorted(without):
			response = without[key]
			if isinstance(response, dict) and "__skipped__" in response:
				print("SKIP %s -- %s" % (key, response["__skipped__"]))
				continue
			exception = isinstance(response, dict) and response.get("__exception__")
			check(not exception, "%s works with Server Scripts DISABLED" % key, exception or "")

		for key in sorted(without):
			if key not in baseline:
				continue
			if any(isinstance(v, dict) and ("__skipped__" in v or "__exception__" in v)
					for v in (baseline[key], without[key])):
				continue
			same = comparable(baseline[key]) == comparable(without[key])
			check(same, "%s returns IDENTICAL output with and without Server Scripts" % key,
				"output differs -- something still reaches a Server Script")

		# meta.api_method must name the app, not the legacy script: it is what
		# a diagnostician reads to tell which layer answered.
		for number in CRITERIA:
			response = without.get("criterion_%s" % number) or {}
			meta = response.get("meta") or {}
			method = meta.get("api_method") or ""
			check(method.startswith("ucc_intelligence."),
				"criterion %s reports its real serving method (%s)" % (number, method or "missing"),
				"still reports %r" % method)

	finally:
		if was_enabled:
			print("\n--- Restoring Server Scripts to their original state ---")
			set_disabled(was_enabled, False)
			for row in ucc_server_scripts():
				print("   %-50s disabled=%s" % (row["name"], row["disabled"]))
			print("Restored: %s" % was_enabled)

	passed = sum(1 for ok, _, _ in results if ok)
	print("\n" + "=" * 72)
	print("%s -- %d/%d checks" % ("PASS" if passed == len(results) else "FAIL", passed, len(results)))
	if passed != len(results):
		print("\nFailures:")
		for ok, message, detail in results:
			if not ok:
				print("  - %s%s" % (message, ("  [%s]" % detail) if detail else ""))
	print("=" * 72)
	return passed == len(results)


ASK_RECORDS = {}
run()
