import frappe


@frappe.whitelist()
def health_check():
	"""Confirm the app is installed and reachable. No business data, no auth bypass."""
	return {
		"ok": True,
		"app": "ucc_intelligence",
		"user": frappe.session.user,
	}
