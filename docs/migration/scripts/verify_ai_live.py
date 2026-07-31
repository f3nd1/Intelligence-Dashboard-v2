"""Prove, on the real bench against the real provider, that Ask UCC's AI
layer actually produces AI text -- and that a facts-only answer is visibly
different from an AI-backed one.

Everything else in this repo's suite proves the wiring with a local HTTP
server (tools/test_ai_client_live_http.py). This is the one check that
spends a real API call against UCC's real account, so it lives here as a
bench script rather than in the automated suite.

PREREQUISITES
  1. site_config.json contains the ROTATED key:
         bench --site <site> set-config ucc_intelligence_ai_api_key "<new key>"
     (This writes to site_config.json. Do not put the key on the Settings
     form -- the form now refuses key-shaped values outright.)
  2. UCC Intelligence Settings has: Enable AI = on, AI Provider = OpenAI,
     AI Model = one of the values "Fetch Available Models" returned.

RUN
    bench --site <site> console
    >>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/verify_ai_live.py").read(), globals())

  The `globals()` argument matters -- without it the top-level defs land in
  locals and cross-function calls raise NameError. Same footgun as
  build_admission_intelligence_embed.py.

WHAT IT PROVES
  - the models endpoint answers with the real account's models
  - a real completion returns real generated text, with real token usage
  - the SAME question with AI off returns the same facts and no AI text,
    so "AI added something" is demonstrable rather than assumed
  - the key is never echoed into any output this script prints

It never prints the key, and never writes it anywhere.
"""

import json

import frappe

from ucc_intelligence.ai import client as ai_client
from ucc_intelligence.ai import orchestration


def redact(text):
	"""Belt and braces: even though nothing here should carry the key, the
	output of this script gets pasted into chat."""
	key = frappe.conf.get(ai_client.AI_API_KEY_SITE_CONFIG_KEY) or ""
	out = str(text)
	return out.replace(key, "<redacted>") if key else out


def stage_1_config():
	print("\n--- Stage 1: configuration ---")
	settings = frappe.get_single("UCC Intelligence Settings")
	key_present = bool(frappe.conf.get(ai_client.AI_API_KEY_SITE_CONFIG_KEY))
	print("  enable_ai              :", bool(settings.enable_ai))
	print("  ai_provider            :", settings.ai_provider)
	print("  ai_model               :", settings.ai_model)
	print("  site_config key present:", key_present, "(value never printed)")
	if not key_present:
		print("  STOP: set ucc_intelligence_ai_api_key in site_config.json first.")
		return False
	if not settings.enable_ai:
		print("  STOP: Enable AI is off, so this would only prove the disabled path.")
		return False
	return True


def stage_2_models():
	print("\n--- Stage 2: real models endpoint ---")
	result = ai_client.list_models()
	if not result.get("ok"):
		print("  FAILED:", redact(result.get("message")))
		return False
	models = result["models"]
	print("  %d chat-capable models returned, e.g. %s" % (len(models), models[:5]))
	settings = frappe.get_single("UCC Intelligence Settings")
	if settings.ai_model and settings.ai_model not in models:
		print("  WARNING: configured model %r is not in the returned list." % settings.ai_model)
	return True


def stage_3_real_completion():
	print("\n--- Stage 3: real completion ---")
	result = ai_client.complete(
		"You are Ask UCC. Answer using ONLY the supplied facts.",
		"QUESTION: What is this student's nationality?\n\nFACTS (JSON):\n"
		+ json.dumps({"get_student_profile": {"student_name": "Test Student", "nationality": "Singaporean"}}),
	)
	if not result.get("ok"):
		print("  FAILED:", redact(result.get("message")))
		return False
	print("  model returned :", result["model"])
	print("  latency        : %d ms" % result["latency_ms"])
	print("  tokens used    :", result["token_usage"])
	print("  GENERATED TEXT :", redact(result["text"]))
	return True


def stage_4_ai_on_vs_off(module_key, record_name, question):
	"""The comparison that actually answers "is AI doing anything?"."""
	print("\n--- Stage 4: same question, AI on vs AI off ---")
	print("  module=%s record=%s" % (module_key, record_name))
	print("  question=%r" % question)

	settings = frappe.get_single("UCC Intelligence Settings")
	original = settings.enable_ai

	try:
		settings.enable_ai = 1
		settings.save(ignore_permissions=False)
		frappe.db.commit()
		with_ai = orchestration.ask(module_key, question, record_name)

		settings.enable_ai = 0
		settings.save(ignore_permissions=False)
		frappe.db.commit()
		without_ai = orchestration.ask(module_key, question, record_name)
	finally:
		settings = frappe.get_single("UCC Intelligence Settings")
		settings.enable_ai = original
		settings.save(ignore_permissions=False)
		frappe.db.commit()

	print("\n  WITH AI    ai_status=%s" % with_ai["ai_status"])
	print("             answer   =%s" % redact((with_ai.get("answer") or {}).get("text")))
	print("  WITHOUT AI ai_status=%s" % without_ai["ai_status"])
	print("             answer   =%s" % ((without_ai.get("answer") or {}).get("text")))
	print("\n  facts identical in both: %s" % (with_ai["facts"] == without_ai["facts"]))

	ok = (
		with_ai["ai_status"] == "available"
		and (with_ai.get("answer") or {}).get("text")
		and without_ai["ai_status"] == "disabled"
		and not without_ai.get("answer")
		and with_ai["facts"] == without_ai["facts"]
	)
	print("\n  RESULT: %s" % (
		"AI genuinely adds interpretation on top of unchanged facts."
		if ok else
		"NOT PROVEN -- read the statuses above; with_ai must be 'available' with text."))
	return ok


def run(module_key="student_journey", record_name=None, question="What is this student's nationality?"):
	if not stage_1_config():
		return
	if not stage_2_models():
		return
	if not stage_3_real_completion():
		return
	if not record_name:
		doctype = orchestration.MODULES[module_key]["doctype"]
		names = frappe.get_all(doctype, pluck="name", limit=1)
		if not names:
			print("\nNo %s records readable by this user -- pass record_name= explicitly." % doctype)
			return
		record_name = names[0]
	stage_4_ai_on_vs_off(module_key, record_name, question)


run()
