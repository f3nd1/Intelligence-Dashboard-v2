"""Which tabs carry painted charts, and which of those embed a dashboard.

Read-only. Nothing is written, nothing is deleted -- run it before the
migrate that deletes the hidden charts to have a record of what was there,
and again afterwards to prove they are gone.

    bench --site ucc-sms-v2.orb.local console
    >>> exec(open("apps/ucc_intelligence/../../docs/migration/scripts/report_embedded_tab_charts.py").read())

The two groups it separates matter:

  WILL BE DELETED   a tab that embeds a dashboard AND still stores painted
                    charts. Nobody can see these -- the embed is what renders
                    -- so they are unreachable configuration.

  UNTOUCHED         a tab with charts and no dashboard. Those charts are on
                    screen and working. They are deleted only if that tab is
                    later given a dashboard, and the audit trail records it.
"""

import json

import frappe

DOCTYPE = "UCC Analytics Tab"


def chart_ids(raw):
	try:
		items = json.loads(raw or "[]")
	except (ValueError, TypeError):
		return ["<unreadable>"]
	return [item.get("chart") for item in items
		if isinstance(item, dict) and item.get("chart")]


rows = frappe.get_all(DOCTYPE, fields=["name", "criterion", "tab", "charts",
	"embedded_dashboard"], order_by="criterion asc, tab asc")

hidden, visible, embeds = [], [], 0
for row in rows:
	ids = chart_ids(row.get("charts"))
	if row.get("embedded_dashboard"):
		embeds += 1
		if ids:
			hidden.append((row["criterion"], row["tab"], row["embedded_dashboard"], ids))
	elif ids:
		visible.append((row["criterion"], row["tab"], ids))

print("=" * 74)
print("UCC Analytics Tab records: %d   embedding a dashboard: %d" % (len(rows), embeds))
print("=" * 74)

print("\nHIDDEN UNDER AN EMBED -- these are what the migrate deletes (%d tab(s))"
	% len(hidden))
if not hidden:
	print("  (none -- either already cleaned up, or none ever existed)")
for criterion, tab, dashboard, ids in hidden:
	print("  %-14s %-10s dashboard %-14s %d chart(s): %s"
		% (criterion, tab, dashboard, len(ids), ", ".join(ids)))

print("\nSTILL ON SCREEN -- charts with no dashboard, left alone (%d tab(s))"
	% len(visible))
if not visible:
	print("  (none)")
for criterion, tab, ids in visible:
	print("  %-14s %-10s %d chart(s): %s" % (criterion, tab, len(ids), ", ".join(ids)))

print("\n" + "=" * 74)
print("Deleted by the migrate: %d chart(s) across %d tab(s)"
	% (sum(len(ids) for _, _, _, ids in hidden), len(hidden)))
print("Run this again after `bench --site ucc-sms-v2.orb.local migrate`.")
print("The first list must then be empty. If it is not, the deletion did not run.")
print("=" * 74)
