#!/usr/bin/env python3
"""Self-check for the UCC Dashboard Access resolution logic.

Executes the real helper functions from the Server Script against a stubbed
frappe, so the union/default/fail-open rules are verified as written.

    python3 tools/test_dashboard_access.py
"""
import pathlib
import re

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "server-scripts" / "UCC Dashboard Access.py"
source = SCRIPT.read_text(encoding="utf-8")

# Load everything up to the trailing dispatch block (which needs a live frappe).
body = source[: source.index("\ntry:\n    frappe.response")]


class Frappe:
    def __init__(self, roles, rows, explode=False):
        self._roles = roles
        self._rows = rows
        self._explode = explode
        self.session = type("S", (), {"user": "someone@example.com"})()
        self.utils = type("U", (), {"now": staticmethod(lambda: "2026-07-25 00:00:00")})()

    def get_roles(self):
        return list(self._roles)

    def get_all(self, doctype, **kwargs):
        if self._explode:
            raise RuntimeError("no read access to UCC Dashboard Access")
        return [dict(r) for r in self._rows]


def load(roles, rows, explode=False):
    scope = {"frappe": Frappe(roles, rows, explode)}
    exec(compile(body, "access", "exec"), scope)  # noqa: S102 - code under test
    return scope


def row(role, **kw):
    base = {
        "name": "row-" + role, "role": role, "enabled": 1,
        "default_when_unconfigured": kw.pop("default", None),
        "show_analytics": 0, "show_explore": 0, "show_ask_ucc": 0,
    }
    for n in range(1, 8):
        base["show_criterion_%d" % n] = 0
    base.update(kw)
    return base


def visible_criteria(payload):
    return sorted(k for k, v in payload["criteria"].items() if v)


def visible_workspaces(payload):
    return sorted(k for k, v in payload["workspaces"].items() if v)


# (a) a role WITH a configured row -> exactly what that row allows
s = load(["Academic Manager", "All"], [
    row("Academic Manager", show_analytics=1, show_criterion_5=1, show_criterion_1=1)
])
r = s["build_response"]()
assert r["applied"] == "role_configuration", r["applied"]
assert visible_criteria(r) == ["criterion_1", "criterion_5"], visible_criteria(r)
assert visible_workspaces(r) == ["analytics"], visible_workspaces(r)
assert r["matched_roles"] == ["Academic Manager"]

# (b) role with NO row, default "Show everything" -> all visible
s = load(["Nobody"], [row("Academic Manager", default="Show everything", show_criterion_1=1)])
r = s["build_response"]()
assert r["applied"] == "default_show_everything", r["applied"]
assert len(visible_criteria(r)) == 7
assert len(visible_workspaces(r)) == 3

# (c) role with NO row, default "Show nothing" -> nothing visible
s = load(["Nobody"], [row("Academic Manager", default="Show nothing", show_criterion_1=1)])
r = s["build_response"]()
assert r["applied"] == "default_show_nothing", r["applied"]
assert visible_criteria(r) == []
assert visible_workspaces(r) == []

# (d) MULTIPLE roles -> union, never intersection
s = load(["Role A", "Role B"], [
    row("Role A", show_analytics=1, show_criterion_1=1, show_criterion_2=1),
    row("Role B", show_ask_ucc=1, show_criterion_2=1, show_criterion_7=1),
])
r = s["build_response"]()
assert visible_criteria(r) == ["criterion_1", "criterion_2", "criterion_7"], visible_criteria(r)
assert visible_workspaces(r) == ["analytics", "ask"], visible_workspaces(r)
assert sorted(r["matched_roles"]) == ["Role A", "Role B"]

# a restrictive row must not subtract from a permissive one
s = load(["Role A", "Role B"], [
    row("Role A", show_criterion_1=1, show_criterion_2=1, show_criterion_3=1),
    row("Role B"),  # grants nothing
])
assert visible_criteria(s["build_response"]()) == ["criterion_1", "criterion_2", "criterion_3"]

# ambiguous default (rows disagree) -> safer "Show everything"
s = load(["Nobody"], [
    row("Role A", default="Show nothing"),
    row("Role B", default="Show everything"),
])
r = s["build_response"]()
assert r["default_ambiguous"] is True
assert r["applied"] == "default_show_everything", r["applied"]
assert len(visible_criteria(r)) == 7

# no row sets a default at all -> "Show everything"
s = load(["Nobody"], [row("Role A"), row("Role B")])
r = s["build_response"]()
assert r["default_ambiguous"] is False
assert r["applied"] == "default_show_everything"

# every row agreeing on "Show nothing" is honoured
s = load(["Nobody"], [
    row("Role A", default="Show nothing"),
    row("Role B", default="Show nothing"),
])
assert s["build_response"]()["applied"] == "default_show_nothing"

# no configuration rows at all -> everything
s = load(["Anyone"], [])
r = s["build_response"]()
assert r["applied"] == "default_show_everything"
assert len(visible_criteria(r)) == 7

# (e) lookup failure -> fail open regardless of configured default
s = load(["Nobody"], [row("Role A", default="Show nothing")], explode=True)
try:
    s["build_response"]()
    raise AssertionError("expected the stubbed read to raise")
except RuntimeError:
    pass
fallback = s["everything_visible"]()
assert sorted(fallback["criteria"].values()) == [True] * 7
assert sorted(fallback["workspaces"].values()) == [True] * 3
assert "except Exception as error:" in source and "error_fail_open" in source, \
    "the dispatch block must catch and fail open"

# checkbox truthiness: Frappe may send 1/0, "1"/"0", True/False
s = load(["R"], [row("R", show_criterion_1="1", show_criterion_2=True, show_criterion_3="0")])
assert visible_criteria(s["build_response"]()) == ["criterion_1", "criterion_2"]

# disabled rows are excluded by the query filter, not by client logic
assert '"enabled": 1' in source, "must filter enabled rows server-side"

# this feature must never touch the data-permission system
for banned in ("has_permission", "frappe.get_doc(", "frappe.db.sql"):
    assert banned not in source, f"unexpected data-permission surface: {banned}"

print("PASS: dashboard access resolution (a-e + defaults, truthiness, union) - 14 scenarios")
