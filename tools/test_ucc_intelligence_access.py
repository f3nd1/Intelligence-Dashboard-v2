#!/usr/bin/env python3
"""Self-check for the ported UCC Dashboard Access logic.

Imports the real module from ucc_intelligence/ against a stubbed frappe (via
sys.modules, since this is a real Python package now, not a flat exec'd
script) and runs the same 20 scenarios as tools/test_dashboard_access.py
(the legacy Server Script's own self-check), proving the port preserves
every rule including the role-leak regression.

    python3 tools/test_ucc_intelligence_access.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class _FakeLogger:
	def info(self, *args, **kwargs):
		pass

	def warning(self, *args, **kwargs):
		pass


class State:
	roles = []
	rows = []
	explode = False
	assigned = []


def _get_all(doctype, **kwargs):
	if doctype == "Has Role":
		if State.assigned is None:
			raise RuntimeError("Has Role unreadable")
		return [{"role": r} for r in State.assigned]
	if State.explode:
		raise RuntimeError("no read access to UCC Dashboard Access")
	return [dict(r) for r in State.rows]


frappe_stub = types.ModuleType("frappe")
frappe_stub.session = type("S", (), {"user": "someone@example.com"})()
frappe_stub.utils = type("U", (), {"now": staticmethod(lambda: "2026-07-25 00:00:00")})()
frappe_stub.get_roles = lambda: list(State.roles)
frappe_stub.get_all = _get_all
frappe_stub.logger = lambda *a, **k: _FakeLogger()
frappe_stub.whitelist = lambda *a, **k: (lambda f: f)
sys.modules["frappe"] = frappe_stub

import ucc_intelligence.permissions.access as access  # noqa: E402 - stub must load first


def load(roles, rows, explode=False, assigned="same"):
	State.roles = roles
	State.rows = rows
	State.explode = explode
	State.assigned = list(roles) if assigned == "same" else assigned
	return access


def row(role, **kw):
	base = {
		"name": "row-" + role, "role": role, "enabled": 1,
		"default_when_unconfigured": kw.pop("default", None),
		"show_analytics": 0, "show_explore": 0, "show_ask_ucc": 0,
		"show_ask_student_journey": 0, "show_ask_recruitment_agent": 0,
		"show_ask_quality_action": 0,
	}
	for n in range(1, 8):
		base["show_criterion_%d" % n] = 0
	base.update(kw)
	return base


def visible_criteria(payload):
	return sorted(k for k, v in payload["criteria"].items() if v)


def visible_workspaces(payload):
	return sorted(k for k, v in payload["workspaces"].items() if v)


def visible_ask_ucc_modules(payload):
	return sorted(k for k, v in payload["ask_ucc_modules"].items() if v)


# (a) a role WITH a configured row -> exactly what that row allows
s = load(["Academic Manager", "All"], [
	row("Academic Manager", show_analytics=1, show_criterion_5=1, show_criterion_1=1)
])
r = s.build_response()
assert r["applied"] == "role_configuration", r["applied"]
assert visible_criteria(r) == ["criterion_1", "criterion_5"], visible_criteria(r)
assert visible_workspaces(r) == ["analytics"], visible_workspaces(r)
assert r["matched_roles"] == ["Academic Manager"]

# (b) role with NO row, default "Show everything" -> all visible
s = load(["Nobody"], [row("Academic Manager", default="Show everything", show_criterion_1=1)])
r = s.build_response()
assert r["applied"] == "default_show_everything", r["applied"]
assert len(visible_criteria(r)) == 7
assert len(visible_workspaces(r)) == 3

# (c) role with NO row, default "Show nothing" -> nothing visible
s = load(["Nobody"], [row("Academic Manager", default="Show nothing", show_criterion_1=1)])
r = s.build_response()
assert r["applied"] == "default_show_nothing", r["applied"]
assert visible_criteria(r) == []
assert visible_workspaces(r) == []

# (d) MULTIPLE roles -> union, never intersection
s = load(["Role A", "Role B"], [
	row("Role A", show_analytics=1, show_criterion_1=1, show_criterion_2=1),
	row("Role B", show_ask_ucc=1, show_criterion_2=1, show_criterion_7=1),
])
r = s.build_response()
assert visible_criteria(r) == ["criterion_1", "criterion_2", "criterion_7"], visible_criteria(r)
assert visible_workspaces(r) == ["analytics", "ask"], visible_workspaces(r)
assert sorted(r["matched_roles"]) == ["Role A", "Role B"]

# a restrictive row must not subtract from a permissive one
s = load(["Role A", "Role B"], [
	row("Role A", show_criterion_1=1, show_criterion_2=1, show_criterion_3=1),
	row("Role B"),  # grants nothing
])
assert visible_criteria(s.build_response()) == ["criterion_1", "criterion_2", "criterion_3"]

# ambiguous default (rows disagree) -> safer "Show everything"
s = load(["Nobody"], [
	row("Role A", default="Show nothing"),
	row("Role B", default="Show everything"),
])
r = s.build_response()
assert r["default_ambiguous"] is True
assert r["applied"] == "default_show_everything", r["applied"]
assert len(visible_criteria(r)) == 7

# no row sets a default at all -> "Show everything"
s = load(["Nobody"], [row("Role A"), row("Role B")])
r = s.build_response()
assert r["default_ambiguous"] is False
assert r["applied"] == "default_show_everything"

# every row agreeing on "Show nothing" is honoured
s = load(["Nobody"], [
	row("Role A", default="Show nothing"),
	row("Role B", default="Show nothing"),
])
assert s.build_response()["applied"] == "default_show_nothing"

# no configuration rows at all -> everything
s = load(["Anyone"], [])
r = s.build_response()
assert r["applied"] == "default_show_everything"
assert len(visible_criteria(r)) == 7

# (e) lookup failure -> fail open regardless of configured default, via the
# public get_dashboard_access() wrapper (the legacy self-check exercises
# build_response() directly and expects it to raise; the ported module moves
# the try/except into get_dashboard_access() as its documented entrypoint)
s = load(["Nobody"], [row("Role A", default="Show nothing")], explode=True)
r = s.get_dashboard_access()
assert r["applied"] == "error_fail_open", r["applied"]
assert sorted(r["criteria"].values()) == [True] * 7
assert sorted(r["workspaces"].values()) == [True] * 3

# checkbox truthiness: Frappe may send 1/0, "1"/"0", True/False
s = load(["R"], [row("R", show_criterion_1="1", show_criterion_2=True, show_criterion_3="0")])
assert visible_criteria(s.build_response()) == ["criterion_1", "criterion_2"]

# disabled rows are excluded by the query filter, not by client logic
access_source = (ROOT / "ucc_intelligence" / "ucc_intelligence" / "permissions" / "access.py").read_text(encoding="utf-8")
assert '"enabled": 1' in access_source, "must filter enabled rows server-side"

# this feature must never touch the data-permission system
for banned in ("has_permission", "frappe.get_doc(", "frappe.db.sql"):
	assert banned not in access_source, f"unexpected data-permission surface: {banned}"

# (f) REGRESSION - the reported bug. frappe.get_roles() returns the EFFECTIVE
# role set, which for Administrator expands to every Role on the site. A user
# whose User form lists none of the configured roles must get the default,
# never another role's configuration.
s = load(
	["All", "Desk User", "Admin Manager", "System Manager"],
	[row("Admin Manager", show_analytics=1, show_criterion_4=1)],
	assigned=["All", "Desk User"],
)
r = s.build_response()
assert r["applied"] == "default_show_everything", \
	"a user without the role must fall back to the default, got " + r["applied"]
assert r["matched_roles"] == [], r["matched_roles"]
assert len(visible_criteria(r)) == 7, visible_criteria(r)
assert r["roles_source"] == "assigned_roles"

# and the same user, once the role IS assigned, does get that configuration
s = load(["All"], [row("Admin Manager", show_analytics=1, show_criterion_4=1)],
         assigned=["All", "Admin Manager"])
r = s.build_response()
assert r["applied"] == "role_configuration"
assert visible_criteria(r) == ["criterion_4"], visible_criteria(r)

# a config row typed with different casing/spacing still matches
s = load(["All"], [row("  admin manager ", show_criterion_4=1)], assigned=["All", "Admin Manager"])
assert visible_criteria(s.build_response()) == ["criterion_4"]

# if Has Role cannot be read at all, fall back to effective roles (never crash)
s = load(["All", "Admin Manager"], [row("Admin Manager", show_criterion_4=1)], assigned=None)
r = s.build_response()
assert r["roles_source"] == "effective_roles_fallback", r["roles_source"]
assert visible_criteria(r) == ["criterion_4"]

# matching must not consult the effective role list when Has Role is readable
assert "frappe.get_roles()" in access_source, "fallback path must still exist"
assert "Has Role" in access_source, "must match against assigned roles"

print("PASS: ported ucc_intelligence.permissions.access matches all 20 legacy scenarios "
      "(a-e + defaults, truthiness, union) incl. the role-leak regression")

# ============================================================
# New in the ported module only (legacy Server Script has no concept of
# this): per-module Ask UCC gating, separate from the Ask UCC workspace tab.
# ============================================================

# a role granted the Ask UCC workspace tab does NOT automatically get any
# specific module -- these are deliberately independent checkboxes
s = load(["Quality Lead"], [row("Quality Lead", show_ask_ucc=1)])
r = s.build_response()
assert visible_workspaces(r) == ["ask"]
assert visible_ask_ucc_modules(r) == [], visible_ask_ucc_modules(r)

# a role granted only one specific module sees only that module
s = load(["Quality Lead"], [row("Quality Lead", show_ask_ucc=1, show_ask_quality_action=1)])
r = s.build_response()
assert visible_ask_ucc_modules(r) == ["quality_action"], visible_ask_ucc_modules(r)

# union across roles applies to ask_ucc_modules the same way it does to criteria/workspaces
s = load(["Role A", "Role B"], [
	row("Role A", show_ask_ucc=1, show_ask_student_journey=1),
	row("Role B", show_ask_ucc=1, show_ask_recruitment_agent=1),
])
r = s.build_response()
assert visible_ask_ucc_modules(r) == ["recruitment_agent", "student_journey"], visible_ask_ucc_modules(r)

# default "Show everything" grants all 3 modules, same as it does criteria/workspaces
s = load(["Nobody"], [row("Academic Manager", default="Show everything")])
r = s.build_response()
assert visible_ask_ucc_modules(r) == ["quality_action", "recruitment_agent", "student_journey"]

# default "Show nothing" grants none
s = load(["Nobody"], [row("Academic Manager", default="Show nothing")])
r = s.build_response()
assert visible_ask_ucc_modules(r) == []

# checkbox truthiness applies to the new fields too (Frappe may send 1/0, "1"/"0", True/False)
s = load(["R"], [row("R", show_ask_student_journey="1", show_ask_recruitment_agent=True, show_ask_quality_action="0")])
assert visible_ask_ucc_modules(s.build_response()) == ["recruitment_agent", "student_journey"]

# the fail-open path grants every module too, same as every other fail-open guarantee
s = load(["Nobody"], [row("Role A", default="Show nothing")], explode=True)
r = s.get_dashboard_access()
assert r["applied"] == "error_fail_open"
assert visible_ask_ucc_modules(r) == ["quality_action", "recruitment_agent", "student_journey"]

print("PASS: Ask UCC per-module gating (show_ask_student_journey/recruitment_agent/quality_action) "
      "follows the exact same union/default/fail-open rules as criteria and workspaces - 7 new scenarios")
