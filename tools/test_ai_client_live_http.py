#!/usr/bin/env python3
"""End-to-end check of ai/client.py over REAL HTTP.

Everything the ordinary suite covers about the AI client is stubbed at
`frappe.make_post_request`, which proves the orchestration around the call
but not the call. This runs the real thing: a real HTTP server on a real
socket, real `requests` doing a real POST/GET with a real Authorization
header, real JSON, and client.py's real parsing and error classification.
The only thing it does not exercise is OpenAI's own service -- for that,
see tools/verify_ai_live.py, which needs a real key on the bench.

Why this matters here: the reported symptom was "Enable AI is on and no AI
text ever appears". That is a wiring question, and wiring is exactly what a
stubbed transport cannot answer.

    python3 tools/test_ai_client_live_http.py
"""
import http.server
import json
import pathlib
import sys
import threading
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ucc_intelligence"))

try:
	import requests
except ImportError:
	print("SKIP: `requests` is not installed; this check needs a real HTTP client.")
	raise SystemExit(0)

checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(ok)
	return ok


# ============================================================
# A fake provider that behaves like a real one over the wire.
# ============================================================
class State:
	mode = "ok"
	seen_auth = []
	seen_body = []


class Handler(http.server.BaseHTTPRequestHandler):
	def log_message(self, *args):
		pass

	def _send(self, code, payload):
		body = json.dumps(payload).encode()
		self.send_response(code)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def do_GET(self):
		State.seen_auth.append(self.headers.get("Authorization"))
		if State.mode == "unauthorized":
			return self._send(401, {"error": {"message": "Incorrect API key provided", "code": "invalid_api_key"}})
		self._send(200, {"data": [
			{"id": "gpt-4o-mini", "object": "model"},
			{"id": "gpt-4o", "object": "model"},
			{"id": "text-embedding-3-small", "object": "model"},
			{"id": "whisper-1", "object": "model"},
			{"id": "dall-e-3", "object": "model"},
		]})

	def do_POST(self):
		State.seen_auth.append(self.headers.get("Authorization"))
		length = int(self.headers.get("Content-Length") or 0)
		State.seen_body.append(json.loads(self.rfile.read(length) or b"{}"))
		if State.mode == "unauthorized":
			return self._send(401, {"error": {"message": "Incorrect API key provided", "code": "invalid_api_key"}})
		if State.mode == "malformed":
			return self._send(200, {"nothing": "useful"})
		self._send(200, {
			"model": "gpt-4o-mini-2024-07-18",
			"choices": [{"message": {"role": "assistant",
				"content": "Mei Lim's nationality is recorded as Singaporean."}}],
			"usage": {"total_tokens": 42},
		})


server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % server.server_address[1]


# ============================================================
# Stub frappe -- but NOT the transport. make_post_request /
# make_get_request are the real thing, implemented the way Frappe
# implements them (requests + raise_for_status + .json()).
# ============================================================
class Conf(dict):
	pass


def make_post_request(url, headers=None, data=None, timeout=None, **kwargs):
	response = requests.post(url, headers=headers, data=data, timeout=timeout)
	response.raise_for_status()
	return response.json()


def make_get_request(url, headers=None, timeout=None, **kwargs):
	response = requests.get(url, headers=headers, timeout=timeout)
	response.raise_for_status()
	return response.json()


class FakeSettings:
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


frappe_stub = types.ModuleType("frappe")
frappe_stub.conf = Conf()
frappe_stub.make_post_request = make_post_request
frappe_stub.make_get_request = make_get_request
frappe_stub._settings = None
frappe_stub.get_single = lambda doctype: frappe_stub._settings
utils = types.ModuleType("frappe.utils")
utils.cstr = lambda v: "" if v is None else str(v)
utils.cint = lambda v: int(v) if str(v or "").strip().lstrip("-").isdigit() else 0
frappe_stub.utils = utils
sys.modules["frappe"] = frappe_stub
sys.modules["frappe.utils"] = utils

from ucc_intelligence.ai import client as ai_client  # noqa: E402

ai_client.OPENAI_CHAT_COMPLETIONS_URL = BASE + "/v1/chat/completions"
ai_client.OPENAI_MODELS_URL = BASE + "/v1/models"

REAL_LOOKING_KEY = "sk-" + "T" * 40  # shape only; never a real credential
frappe_stub.conf[ai_client.AI_API_KEY_SITE_CONFIG_KEY] = REAL_LOOKING_KEY
frappe_stub._settings = FakeSettings(
	enable_ai=1, ai_provider="OpenAI", ai_model="gpt-4o-mini",
	max_output_tokens=500, default_temperature=0.2, ai_request_timeout_seconds=10,
)


# ============================================================
# complete() -- a real request that really returns AI text
# ============================================================
State.mode = "ok"
result = ai_client.complete("You are Ask UCC.", "QUESTION: nationality?\n\nFACTS (JSON):\n{}")
report(result["ok"] is True, "complete() succeeds against a real HTTP provider")
report(result["text"] == "Mei Lim's nationality is recorded as Singaporean.",
	"the provider's actual generated text is returned, parsed off the wire")
report(result["model"] == "gpt-4o-mini-2024-07-18",
	"the model the provider REPORTS is returned, not the one we asked for")
report(result["token_usage"] == 42, "token usage is read from the real response")
report(isinstance(result["latency_ms"], int), "latency is measured around the real call")

report(State.seen_auth[-1] == "Bearer " + REAL_LOOKING_KEY,
	"the key travels only in the Authorization header of the server-side request")
sent = State.seen_body[-1]
report(sent["model"] == "gpt-4o-mini", "the configured model is sent")
report(sent["temperature"] == 0.2 and sent["max_tokens"] == 500,
	"the configured temperature and token cap are sent")
report([m["role"] for m in sent["messages"]] == ["system", "user"],
	"system and user prompts are sent as separate messages, per the prompt-injection boundary")

# ============================================================
# list_models() -- a real GET, really filtered
# ============================================================
models = ai_client.list_models()
report(models["ok"] is True, "list_models() succeeds against a real HTTP provider")
report(models["models"] == ["gpt-4o", "gpt-4o-mini"],
	"only chat-capable models are offered -- embeddings/whisper/dall-e are filtered out")

# ============================================================
# Failure modes: visible, classified, never a crash and never a leak
# ============================================================
State.mode = "unauthorized"
bad = ai_client.complete("s", "u")
report(bad["ok"] is False and bad["status"] == "error",
	"a real 401 from the provider is reported, not raised")
report("unauthorized" in bad["message"].lower() or "api key" in bad["message"].lower(),
	"the 401 is classified into an actionable message")
report(REAL_LOOKING_KEY not in json.dumps(bad),
	"the key NEVER appears in the returned error, even though it was in the request headers")

bad_models = ai_client.list_models()
report(bad_models["ok"] is False, "list_models() reports a bad key instead of crashing the form")
report(REAL_LOOKING_KEY not in json.dumps(bad_models), "...and does not leak the key either")

State.mode = "malformed"
malformed = ai_client.complete("s", "u")
report(malformed["ok"] is False and "shape" in malformed["message"],
	"a 200 with an unexpected body is reported, not indexed into blindly")

# no key at all
State.mode = "ok"
frappe_stub.conf.pop(ai_client.AI_API_KEY_SITE_CONFIG_KEY)
nokey = ai_client.complete("s", "u")
report(nokey["status"] == "unavailable" and "site_config" in nokey["message"],
	"a missing key names site_config.json -- the exact thing the admin must fix")
report(ai_client.list_models()["status"] == "unavailable",
	"list_models() with no key is unavailable, not an exception")

# the key is re-read per call, never cached at import
frappe_stub.conf[ai_client.AI_API_KEY_SITE_CONFIG_KEY] = "sk-" + "R" * 40
rotated = ai_client.complete("s", "u")
report(rotated["ok"] is True and State.seen_auth[-1] == "Bearer sk-" + "R" * 40,
	"a ROTATED key takes effect on the next call -- the key is read fresh, never cached")

server.shutdown()
passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
