// Copyright (c) 2026, United Ceres College Pte Ltd
// For license information, please see license.txt

frappe.ui.form.on("UCC Intelligence Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Manage Role Access"), () => {
			frappe.set_route("List", "UCC Dashboard Access");
		});
		render_ai_field_indicator(frm);
		render_live_status(frm);
	},
	ai_provider(frm) {
		render_ai_field_indicator(frm);
	},
	ai_model(frm) {
		render_ai_field_indicator(frm);
	},
});

// No server round-trip needed -- this only reads the form's own
// already-loaded fields, not anything that requires a status check.
function render_ai_field_indicator(frm) {
	const filled = Boolean(frm.doc.ai_provider && frm.doc.ai_model);
	frm.dashboard.add_indicator(
		__("AI provider/model fields filled: {0}", [filled ? __("yes") : __("no")]),
		filled ? "green" : "grey"
	);
}

function render_live_status(frm) {
	frappe.call({
		method: "ucc_intelligence.api.get_settings_status",
		callback(response) {
			const status = response && response.message;
			if (!status || !status.ok) {
				frm.dashboard.add_indicator(__("Status check returned no data"), "orange");
				return;
			}

			const charts = status.insights_charts || {};
			frm.dashboard.add_indicator(
				__("Insights charts: {0}/{1} built", [charts.built_count, charts.total_count]),
				charts.built_count === charts.total_count ? "green" : "orange"
			);

			const insightsPerm = status.insights_permission_setting || {};
			frm.dashboard.add_indicator(
				__("Insights permission enforcement: {0}", [insightsPerm.apply_user_permissions ? __("ON") : __("OFF")]),
				insightsPerm.apply_user_permissions ? "green" : "red"
			);

			const access = status.dashboard_access || {};
			frm.dashboard.add_indicator(
				__("Dashboard access roles configured: {0}", [access.configured_role_count || 0]),
				(access.configured_role_count || 0) > 0 ? "green" : "orange"
			);

			const aiConfigured = status.ai_provider_configured || {};
			frm.dashboard.add_indicator(
				__("AI provider configured elsewhere: {0}", [aiConfigured.configured ? __("yes") : __("no")]),
				aiConfigured.configured ? "green" : "grey"
			);

			frm.dashboard.add_indicator(
				__("Site database reachable: {0}", [status.db_reachable ? __("yes") : __("no")]),
				status.db_reachable ? "green" : "red"
			);
		},
		error() {
			frm.dashboard.add_indicator(__("Status check failed to load"), "red");
		},
	});
}
