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
import time

import frappe

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
	try:
		response = frappe.make_post_request(
			OPENAI_CHAT_COMPLETIONS_URL,
			headers={
				"Authorization": "Bearer " + api_key,
				"Content-Type": "application/json",
			},
			data=json.dumps(payload),
			timeout=timeout_seconds,
		)
	except Exception as error:
		# Never let the raw exception (which can embed request headers,
		# including the Authorization header, in some HTTP client error
		# reprs) propagate -- classify and pass through a clean message only.
		return unavailable("error", classify_error(error))
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

	try:
		response = frappe.make_get_request(
			OPENAI_MODELS_URL,
			headers={"Authorization": "Bearer " + api_key},
			timeout=timeout_seconds,
		)
	except Exception as error:
		return unavailable("error", classify_error(error))

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


def classify_error(error):
	text = frappe.utils.cstr(error)
	lowered = text.lower()
	if "timeout" in lowered or "timed out" in lowered:
		return "Request to the AI provider timed out."
	if "401" in text or "unauthorized" in lowered or "invalid_api_key" in lowered:
		return "The AI provider rejected the request as unauthorized -- check the configured API key."
	if "429" in text or "rate limit" in lowered:
		return "The AI provider reported a rate limit."
	return "The AI provider request failed."
