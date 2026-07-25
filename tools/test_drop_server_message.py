#!/usr/bin/env python3
"""Self-check for drop_server_message() in the Criterion 5 Server Script.

Frappe logs a permission message before raising, so catching the exception is
not enough - the message still returns in _server_messages and the Frappe
client pops its own raw dialog. This verifies the helper clears it, and that it
degrades safely on a Frappe build where the API is missing.

    python3 tools/test_drop_server_message.py
"""
import re
import sys
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "server-scripts" / "UCC Analytics - Criterion 5.py"
source = SCRIPT.read_text(encoding="utf-8")

match = re.search(r"^def drop_server_message\(\):.*?(?=^def )", source, re.S | re.M)
assert match, "drop_server_message() not found in the Criterion 5 script"
helper_src = match.group(0)


def build(frappe_obj):
    scope = {"frappe": frappe_obj}
    exec(compile(helper_src, "helper", "exec"), scope)  # noqa: S102 - the helper under test
    return scope["drop_server_message"]


class Modern:
    """Frappe exposing clear_last_message (preferred: drops only that entry)."""
    def __init__(self):
        self.log = ["permission message"]
        self.cleared_all = False

    def clear_last_message(self):
        self.log.pop()

    def clear_messages(self):
        self.cleared_all = True
        self.log = []


class OnlyClearAll:
    """Older Frappe: no clear_last_message, must fall back to clear_messages."""
    def __init__(self):
        self.log = ["permission message"]
        self.used_fallback = False

    def clear_messages(self):
        self.used_fallback = True
        self.log = []


class Neither:
    """Locked-down build: nothing available - must not raise."""
    def __init__(self):
        self.log = ["permission message"]


# 1. preferred path clears just the logged message
m = Modern()
build(m)()
assert m.log == [], "clear_last_message should drop the logged message"
assert m.cleared_all is False, "must not nuke the whole message log when the precise API exists"

# 2. fallback path on older builds
o = OnlyClearAll()
build(o)()
assert o.used_fallback is True, "should fall back to clear_messages"
assert o.log == []

# 3. neither available -> swallowed, never breaks the response
n = Neither()
build(n)()          # must not raise
assert n.log == ["permission message"], "no API means no change, but no crash either"

# 4. an API that itself raises must still be contained
class Exploding:
    def clear_last_message(self):
        raise RuntimeError("boom")

    def clear_messages(self):
        raise RuntimeError("boom")

build(Exploding())()  # must not raise

# 5. the helper must be wired into the paths that swallow permission errors
for fn in ("def get_meta(", "def resolve_source(", "def fetch_rows("):
    start = source.index(fn)
    end = source.index("\ndef ", start + 1)
    assert "drop_server_message()" in source[start:end], f"{fn.strip()} does not clear the message log"

print("PASS: drop_server_message (5 cases, 3 call sites wired)")
