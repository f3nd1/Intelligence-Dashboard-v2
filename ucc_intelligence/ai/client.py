"""The one place an AI provider's API key is ever read or an external AI
HTTP call is ever made (CLAUDE.md Phase 8: "one AI client service").

Reads configuration from two places, deliberately not one:
- `frappe.conf.get("ucc_intelligence_ai_api_key")` for the secret itself --
  never the `UCC Intelligence Settings` DocType, which was deliberately
  built with no field for it (docs/architecture/settings-page-plan.md §2:
  "no AI client exists yet to justify picking a storage mechanism"). This
  module is that client; the key still doesn't live on the DocType. Same
  site_config key name `settings/status.py`'s `get_ai_provider_configured()`
  already checks for presence of, so that indicator goes green the moment
  this is actually configured, no code changes needed there.
- `UCC Intelligence Settings` (provider, model, temperature, timeouts,
  the `enable_ai` toggle) for everything that isn't a secret.

Never logs the API key. Never raises out to callers -- every failure mode
(AI disabled, not configured, provider error, timeout) returns the same
`{"ok": False, "status": ..., "message": ...}` shape, because Ask UCC's
whole design (docs/architecture/ask-ucc-phase-plan.md §2.2) requires
facts-only operation to keep working when AI is unavailable -- an AI
failure must degrade, never crash, the response.
"""

import json
import re
import time

import frappe
import requests

AI_API_KEY_SITE_CONFIG_KEY = "ucc_intelligence_ai_api_key"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS_URL = "https://api.openai.com/v1/models"

DEFAULT_MAX_OUTPUT_TOKENS = 500
DEFAULT_TIMEOUT_SECONDS = 30


def get_settings():
	try:
		return frappe.get_single("UCC Intelligence Settings")
	except Exception:
		return None


def is_enabled():
	settings = get_settings()
	return bool(settings and settings.enable_ai)


def unavailable(status, message):
	return {"ok": False, "status": status, "message": message}


def complete(system_prompt, user_prompt):
	"""Single request/response call -- no streaming, no multi-turn tool use.
	Orchestration (ai/orchestration.py) is responsible for deciding what
	goes into the two prompts; this module only ever talks to the provider.
	"""
	settings = get_settings()
	if not settings:
		return unavailable("unavailable", "UCC Intelligence Settings could not be read.")
	if not settings.enable_ai:
		return unavailable("disabled", "AI is disabled in UCC Intelligence Settings.")
	if not settings.ai_provider or not settings.ai_model:
		return unavailable("unavailable", "AI provider/model are not configured in UCC Intelligence Settings.")

	api_key = frappe.conf.get(AI_API_KEY_SITE_CONFIG_KEY)
	if not api_key:
		return unavailable("unavailable", "No API key configured (site_config.json: %s)." % AI_API_KEY_SITE_CONFIG_KEY)

	# Provider dispatch has exactly one branch today -- ai_provider is free
	# text (settings-page-plan.md §2: which providers are "approved" is
	# still an open institutional decision, not a fixed list this code
	# should imply). Anything other than OpenAI is reported as unavailable
	# rather than guessed at, since there's nothing else implemented yet.
	if frappe.utils.cstr(settings.ai_provider).strip().lower() != "openai":
		return unavailable("unavailable", "AI provider %r has no implementation yet -- only OpenAI is wired up." % settings.ai_provider)

	max_tokens = frappe.utils.cint(settings.max_output_tokens) or DEFAULT_MAX_OUTPUT_TOKENS
	timeout_seconds = frappe.utils.cint(settings.ai_request_timeout_seconds) or DEFAULT_TIMEOUT_SECONDS
	temperature = settings.default_temperature
	if temperature is None:
		temperature = 0.2

	payload = {
		"model": settings.ai_model,
		"messages": [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
		"temperature": temperature,
		"max_tokens": max_tokens,
	}

	started = time.monotonic()
	response, error_message = request_json(
		"POST", OPENAI_CHAT_COMPLETIONS_URL, api_key,
		body=json.dumps(payload), timeout_seconds=timeout_seconds,
	)
	if error_message:
		return unavailable("error", error_message)
	latency_ms = int((time.monotonic() - started) * 1000)

	try:
		text = response["choices"][0]["message"]["content"]
	except Exception:
		return unavailable("error", "Provider response did not contain the expected shape.")

	usage = response.get("usage") or {}
	return {
		"ok": True,
		"text": text,
		"model": response.get("model") or settings.ai_model,
		"latency_ms": latency_ms,
		"token_usage": frappe.utils.cint(usage.get("total_tokens")),
	}


def list_models():
	"""The provider's own model list, so the AI Model field can be a chosen
	value rather than typed text. Same key source and the same never-raise
	contract as complete(): a bad or missing key comes back as a message the
	form can display inline, not an exception that breaks the form.

	Deliberately server-side. The key never reaches the browser -- the client
	gets model ids and nothing else.
	"""
	settings = get_settings()
	provider = frappe.utils.cstr(settings.ai_provider).strip().lower() if settings else ""
	if provider and provider != "openai":
		return unavailable("unavailable", "AI provider %r has no implementation yet -- only OpenAI is wired up." % settings.ai_provider)

	api_key = frappe.conf.get(AI_API_KEY_SITE_CONFIG_KEY)
	if not api_key:
		return unavailable("unavailable", "No API key configured (site_config.json: %s)." % AI_API_KEY_SITE_CONFIG_KEY)

	timeout_seconds = DEFAULT_TIMEOUT_SECONDS
	if settings:
		timeout_seconds = frappe.utils.cint(settings.ai_request_timeout_seconds) or DEFAULT_TIMEOUT_SECONDS

	response, error_message = request_json(
		"GET", OPENAI_MODELS_URL, api_key, timeout_seconds=timeout_seconds,
	)
	if error_message:
		return unavailable("error", error_message)

	rows = (response or {}).get("data")
	if not isinstance(rows, list):
		return unavailable("error", "Provider response did not contain the expected shape.")

	# Chat-completions models only. The endpoint also returns embeddings,
	# audio, image and moderation models, none of which complete() can use --
	# offering them would just produce a confusing 400 later.
	models = sorted(
		row["id"] for row in rows
		if isinstance(row, dict) and isinstance(row.get("id"), str) and is_chat_model(row["id"])
	)
	if not models:
		return unavailable("unavailable", "The provider returned no chat-capable models.")
	return {"ok": True, "models": models}


NON_CHAT_MODEL_MARKERS = ("embedding", "whisper", "tts", "dall-e", "moderation", "audio", "image", "realtime", "transcribe")


def is_chat_model(model_id):
	lowered = model_id.lower()
	if any(marker in lowered for marker in NON_CHAT_MODEL_MARKERS):
		return False
	return lowered.startswith("gpt-") or lowered.startswith("o1") or lowered.startswith("o3") or lowered.startswith("chatgpt")


# Anything key-shaped, not just OUR key. These messages now carry provider
# error bodies and exception text for diagnosability, and a proxy or an
# upstream error can echo back a credential that is not the one we
# configured. Sibling pattern, deliberately stricter because it gates saving
# rather than scrubbing: ucc_intelligence_settings.py's API_KEY_PATTERN.
ANY_API_KEY = re.compile(r"sk-[A-Za-z0-9_\-]{8,}", re.IGNORECASE)


def redact(text, api_key):
	"""Any message leaving this module gets credentials stripped. Error reprs
	from HTTP clients can embed request headers, and the Authorization header
	carries the key."""
	out = frappe.utils.cstr(text)
	if api_key:
		out = out.replace(api_key, "<redacted>")
		# The tail alone is enough to identify a key in a leak report.
		if len(api_key) > 8:
			out = out.replace(api_key[-8:], "<redacted>")
	return ANY_API_KEY.sub("<redacted>", out)


def provider_error_message(status_code, body_text, api_key):
	"""The provider's OWN error, not a generic sentence.

	OpenAI returns {"error": {"message", "type", "code"}}. Surfacing that
	verbatim (minus the key) is the difference between "The AI provider
	request failed" -- which sends someone to a bench console with urllib to
	find out what actually happened -- and a message that names the problem.
	"""
	detail = ""
	try:
		payload = json.loads(body_text or "{}")
		error = payload.get("error") or {}
		detail = error.get("message") or ""
		code = error.get("code") or error.get("type")
		if code:
			detail = "%s (%s)" % (detail, code) if detail else str(code)
	except Exception:
		pass
	if not detail:
		detail = (body_text or "").strip()[:300] or "no response body"
	return redact("The AI provider returned HTTP %s: %s" % (status_code, detail), api_key)


def request_json(method, url, api_key, body=None, timeout_seconds=DEFAULT_TIMEOUT_SECONDS):
	"""One HTTP call to the provider. Returns (parsed_json, error_message);
	exactly one of the two is populated, and it never raises.

	Uses `requests` directly rather than Frappe's make_get_request /
	make_post_request helpers, for two reasons, both learned the hard way:

	1. Those helpers are NOT reliably available as `frappe.make_*`. They
	   live in `frappe.integrations.utils`, and the top-level aliases this
	   module used to call do not exist on every Frappe version -- which
	   raised AttributeError, got swallowed by a bare `except Exception`,
	   and was reported as the generic "The AI provider request failed."
	   A valid key and a reachable network looked identical to a bad key.
	   `requests` is a hard Frappe dependency, so it is always importable
	   and there is no version-dependent name to get wrong.

	2. Those helpers call raise_for_status() and hand back only an
	   exception, discarding the response body -- which is exactly where
	   OpenAI puts the reason. We need the status AND the body to say
	   anything useful.

	The key travels only in the Authorization header and is redacted from
	every message returned.
	"""
	headers = {"Authorization": "Bearer " + api_key}
	if body is not None:
		headers["Content-Type"] = "application/json"

	try:
		response = requests.request(
			method, url, headers=headers, data=body, timeout=timeout_seconds,
		)
	except requests.exceptions.Timeout:
		return None, "Request to the AI provider timed out after %ss." % timeout_seconds
	except requests.exceptions.ConnectionError as error:
		return None, redact("Could not reach the AI provider: %s" % error, api_key)
	except Exception as error:
		# Still never raises out, but no longer anonymous: the exception type
		# is what tells you a misconfiguration from a network fault.
		return None, redact("The AI provider request failed (%s: %s)" % (type(error).__name__, error), api_key)

	if response.status_code >= 400:
		return None, provider_error_message(response.status_code, response.text, api_key)

	try:
		return response.json(), None
	except Exception:
		return None, redact(
			"The AI provider returned HTTP %s with a non-JSON body: %s"
			% (response.status_code, (response.text or "")[:300]),
			api_key,
		)
