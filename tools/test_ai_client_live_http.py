#!/usr/bin/env python3
"""End-to-end check of ai/client.py over REAL HTTP.

A real HTTP server on a real socket, real `requests` doing a real POST/GET
with a real Authorization header, real JSON, and client.py's real parsing
and error handling. Nothing about the transport is stubbed. The only thing
not exercised is OpenAI's own service -- for that see
docs/migration/scripts/verify_ai_live.py, which needs a real key on a bench.

This file previously DEFINED frappe.make_post_request and
frappe.make_get_request in its own stub and then claimed to test the
transport. It was testing a transport it had just written. The real
`frappe` has no such top-level attributes, so client.py raised
AttributeError on every actual call, a bare `except Exception` swallowed
it, and it surfaced as "The AI provider request failed" -- indistinguishable
from a bad key -- while this test stayed green. That is the specific
failure the checks at the bottom now guard against.

Rule this file exists to enforce: a stub must never supply the thing under
test. Stub the surroundings, run the real path.

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
			return self._send(401, {"error": {
				"message": "Incorrect API key provided: %s" % (self.headers.get("Authorization") or "").replace("Bearer ", ""),
				"code": "invalid_api_key",
			}})
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
			# Real providers and gateways DO echo the offending credential
			# back in an error ("Incorrect API key provided: sk-..."), which
			# is exactly the leak redaction exists to stop. Including it here
			# means the redaction assertions below actually get exercised
			# instead of passing vacuously.
			return self._send(401, {"error": {
				"message": "Incorrect API key provided: %s" % (self.headers.get("Authorization") or "").replace("Bearer ", ""),
				"code": "invalid_api_key",
			}})
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
# Stub frappe -- and NOTHING of the transport.
#
# An earlier version of this file DEFINED frappe.make_post_request and
# frappe.make_get_request itself, then congratulated itself on testing the
# transport. It was testing a transport it had just written. The real
# `frappe` has no such top-level attributes -- they live in
# frappe.integrations.utils -- so client.py raised AttributeError on every
# real call, the bare `except Exception` swallowed it, and it surfaced as
# the generic "The AI provider request failed" while this test stayed
# green. A stub that supplies the thing under test proves nothing.
#
# client.py now calls `requests` directly, so this file stubs no transport
# at all and the code exercises exactly the path production uses.
# ============================================================
class Conf(dict):
	pass


class FakeSettings:
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


frappe_stub = types.ModuleType("frappe")
frappe_stub.conf = Conf()
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
report("401" in bad["message"],
	"the message names the actual HTTP STATUS -- diagnosable without a manual urllib test")
report("Incorrect API key provided" in bad["message"],
	"the provider's OWN error text is surfaced, not replaced by a generic sentence")
report("invalid_api_key" in bad["message"],
	"the provider's error code is surfaced too")
report(REAL_LOOKING_KEY not in json.dumps(bad),
	"the key NEVER appears in the returned error, even though it was in the request headers")
report(REAL_LOOKING_KEY[-8:] not in json.dumps(bad),
	"...nor does its tail, which is enough to identify a key in a leak report")

bad_models = ai_client.list_models()
report(bad_models["ok"] is False, "list_models() reports a bad key instead of crashing the form")
report("401" in bad_models["message"] and "Incorrect API key" in bad_models["message"],
	"list_models() surfaces the real status and provider error too")
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

# ============================================================
# THE ROOT CAUSE, guarded so it cannot come back
#
# client.py called frappe.make_post_request / frappe.make_get_request.
# Those are not top-level frappe attributes -- they live in
# frappe.integrations.utils -- so every real call raised AttributeError,
# which the bare `except Exception` turned into "The AI provider request
# failed". A valid key, a correct site_config and a reachable network
# looked exactly like a bad key.
# ============================================================
CLIENT_SOURCE = (pathlib.Path(__file__).resolve().parents[1] / "ucc_intelligence" / "ucc_intelligence"
	/ "ai" / "client.py").read_text(encoding="utf-8")
for banned in ("frappe.make_post_request", "frappe.make_get_request", "frappe.make_put_request"):
	# The CALL, not the mention -- request_json's docstring names these
	# deliberately, to explain why they are not used.
	report("%s(" % banned not in CLIENT_SOURCE,
		"ROOT CAUSE: client.py does not call %s -- it is not a real top-level frappe attribute" % banned)

# The stub frappe in this file deliberately has no transport attributes at
# all. If client.py reaches for one, it gets AttributeError here exactly as
# it did on the bench -- which is the point: the test now fails the same way
# production does, instead of quietly supplying what production lacks.
for banned_attr in ("make_post_request", "make_get_request"):
	report(not hasattr(frappe_stub, banned_attr),
		"the frappe stub does NOT define %s -- a stub that supplies the thing under test proves nothing"
		% banned_attr)

# Prove the stub really would fail the way the bench did, rather than just
# asserting that it lacks the attribute.
try:
	frappe_stub.make_get_request("http://x")
	report(False, "the stub should not have a transport helper to call")
except AttributeError as error:
	report("make_get_request" in str(error),
		"reaching for the old helper raises AttributeError -- the exact failure that was being swallowed")

# A message with no status and no provider text is what sent this to a
# bench console with urllib. An HTTP error must never produce one.
sample = ai_client.provider_error_message(500, '{"error": {"message": "upstream exploded", "code": "server_error"}}', None)
report("500" in sample and "upstream exploded" in sample and "server_error" in sample,
	"an HTTP error message carries the status, the provider's text AND its code")
report("The AI provider request failed." not in sample,
	"...never the bare generic sentence that hid this bug")
report("no response body" in ai_client.provider_error_message(502, "", None),
	"an empty error body says so explicitly rather than rendering an empty message")
report("<html>bad gateway" in ai_client.provider_error_message(502, "<html>bad gateway</html>", None),
	"a non-JSON error body (proxy/gateway HTML) is passed through, not discarded")

server.shutdown()
passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
