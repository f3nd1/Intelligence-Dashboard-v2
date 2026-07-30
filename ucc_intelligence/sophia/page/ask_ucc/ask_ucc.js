// Ask UCC -- the chat surface for ucc_intelligence.api.ask_ucc.
//
// Deliberately minimal but functional, per the plan doc's §2.1 step 8: the
// three zones an answer must be separable into (AI interpretation, the facts
// it was given, the sources those came from) are visually distinct, so a
// reader can always tell which is which. That separation is the whole point
// of the tool-first design -- collapsing them into one prose blob would
// undo it.
//
// Reuses Sophia Analytics' existing visual language rather than inventing a
// second one: the same panel/card classes from sophia_analytics.css and the
// same UCCShared.permissionNoticeHtml() a blocked Analytics source renders
// through. Only the genuinely new chat-specific layout is added as its own
// small stylesheet.

frappe.pages["ask-ucc"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Ask UCC",
		single_column: true,
	});

	// page.body is jQuery-wrapped in this Frappe version, not a raw DOM node
	// -- the same trap sophia_analytics.js documents. Unwrap once here.
	const root = page.body[0] || page.body;

	if (window.UCCShared) {
		boot(root);
	} else {
		frappe.require("/assets/ucc_intelligence/js/shared.js", () => boot(root));
	}
};

const SHELL_HTML = `
<div class="ucc-ask" id="uccAsk">
	<section class="panel ucc-shared-panel ucc-ask-controls">
		<div class="panel-head ucc-card-header">
			<div class="ucc-card-heading-copy">
				<h2>Ask UCC</h2>
				<p class="ucc-card-description">Answers are built from live records you already have permission to see. Facts come from ERPNext; any AI text is labelled separately.</p>
			</div>
		</div>
		<div class="ucc-ask-row">
			<label class="ucc-ask-field">
				<span>Module</span>
				<select data-ask-module></select>
			</label>
			<label class="ucc-ask-field ucc-ask-field-grow">
				<span>Record</span>
				<input type="text" data-ask-record placeholder="Search for a record..." autocomplete="off">
				<div class="ucc-ask-suggestions" data-ask-suggestions hidden></div>
			</label>
		</div>
		<div class="ucc-ask-row">
			<label class="ucc-ask-field ucc-ask-field-grow">
				<span>Question</span>
				<textarea data-ask-question rows="2" placeholder="e.g. Is this ready to close?"></textarea>
			</label>
			<button class="btn btn-primary ucc-ask-submit" data-ask-submit>Ask</button>
		</div>
		<div class="ucc-ask-status" data-ask-status hidden></div>
	</section>

	<section class="ucc-ask-thread" data-ask-thread></section>
</div>
`;

const STYLE_ID = "ucc-ask-style";
const STYLE_TEXT = `
.ucc-ask{display:flex;flex-direction:column;gap:16px;padding:16px}
.ucc-ask-row{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;padding:0 16px 16px}
.ucc-ask-field{display:flex;flex-direction:column;gap:4px;position:relative;min-width:200px}
.ucc-ask-field-grow{flex:1}
.ucc-ask-field>span{font-size:12px;font-weight:600;opacity:.75}
.ucc-ask-field select,.ucc-ask-field input,.ucc-ask-field textarea{padding:8px;border:1px solid var(--border-color,#d1d8dd);border-radius:6px;font:inherit;width:100%}
.ucc-ask-submit{white-space:nowrap}
.ucc-ask-suggestions{position:absolute;top:100%;left:0;right:0;z-index:20;background:var(--card-bg,#fff);border:1px solid var(--border-color,#d1d8dd);border-radius:6px;max-height:240px;overflow:auto;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.ucc-ask-suggestion{padding:8px 10px;cursor:pointer;font-size:13px}
.ucc-ask-suggestion:hover,.ucc-ask-suggestion.is-active{background:var(--bg-light-gray,#f4f5f6)}
.ucc-ask-status{padding:0 16px 16px;font-size:13px}
.ucc-ask-status[data-tone="error"]{color:var(--red-600,#c0392b)}
.ucc-ask-thread{display:flex;flex-direction:column;gap:16px}
.ucc-ask-turn{display:flex;flex-direction:column;gap:12px}
.ucc-ask-question-bubble{align-self:flex-end;max-width:70%;background:var(--bg-light-gray,#f4f5f6);padding:10px 14px;border-radius:12px;font-size:14px}
.ucc-ask-zone{border:1px solid var(--border-color,#d1d8dd);border-radius:8px;overflow:hidden}
.ucc-ask-zone-head{padding:8px 12px;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:var(--bg-light-gray,#f4f5f6)}
.ucc-ask-zone-body{padding:12px}
.ucc-ask-zone-ai .ucc-ask-zone-head{background:#eef4ff;color:#2c5aa0}
.ucc-ask-zone-facts .ucc-ask-zone-head{background:#eefaf1;color:#1e7a45}
.ucc-ask-answer-text{white-space:pre-wrap;font-size:14px;line-height:1.55}
.ucc-ask-fact-group{margin-bottom:12px}
.ucc-ask-fact-group:last-child{margin-bottom:0}
.ucc-ask-fact-group>h4{font-size:12px;margin:0 0 6px;opacity:.8}
.ucc-ask-fact-table{width:100%;border-collapse:collapse;font-size:12px}
.ucc-ask-fact-table th,.ucc-ask-fact-table td{border:1px solid var(--border-color,#e6e9ec);padding:4px 8px;text-align:left;vertical-align:top}
.ucc-ask-fact-table th{width:34%;font-weight:600;opacity:.8}
.ucc-ask-source{display:inline-flex;gap:6px;align-items:center;font-size:12px;padding:4px 8px;border:1px solid var(--border-color,#d1d8dd);border-radius:999px;margin:0 6px 6px 0;text-decoration:none}
.ucc-ask-ai-unavailable{font-size:13px;opacity:.8;font-style:italic}
`;

function injectStyles() {
	if (document.getElementById(STYLE_ID)) return;
	const style = document.createElement("style");
	style.id = STYLE_ID;
	style.textContent = STYLE_TEXT;
	document.head.appendChild(style);
}

function esc(value) {
	return window.UCCShared.escapeHtml(value == null ? "" : String(value));
}

function boot(root) {
	injectStyles();
	root.innerHTML = SHELL_HTML;

	const moduleSelect = root.querySelector("[data-ask-module]");
	const recordInput = root.querySelector("[data-ask-record]");
	const suggestionBox = root.querySelector("[data-ask-suggestions]");
	const questionInput = root.querySelector("[data-ask-question]");
	const submitButton = root.querySelector("[data-ask-submit]");
	const statusNode = root.querySelector("[data-ask-status]");
	const thread = root.querySelector("[data-ask-thread]");

	const state = { modules: [], busy: false };

	function setStatus(text, tone) {
		if (!text) {
			statusNode.hidden = true;
			statusNode.textContent = "";
			return;
		}
		statusNode.hidden = false;
		statusNode.textContent = text;
		statusNode.dataset.tone = tone || "info";
	}

	function currentModule() {
		return state.modules.find((m) => m.key === moduleSelect.value) || null;
	}

	// Which modules this user may see comes from the server
	// (get_dashboard_access's ask_ucc_modules), never from a hardcoded list
	// here -- the same interface-composition rule Analytics follows.
	frappe.call({
		method: "ucc_intelligence.api.get_ask_ucc_modules",
		callback(response) {
			const modules = (response && response.message && response.message.modules) || [];
			state.modules = modules;
			if (!modules.length) {
				moduleSelect.innerHTML = "";
				submitButton.disabled = true;
				recordInput.disabled = true;
				questionInput.disabled = true;
				setStatus("No Ask UCC modules are enabled for your account. Ask an administrator if you need access.", "error");
				return;
			}
			moduleSelect.innerHTML = modules
				.map((m) => `<option value="${esc(m.key)}">${esc(m.label)}</option>`)
				.join("");
		},
		error() {
			setStatus("Could not load the available modules.", "error");
		},
	});

	// --- record picker: a plain search against the module's own DocType,
	// permission-checked server-side by frappe.client.get_list like any
	// other Desk link field. No custom search endpoint needed.
	let searchTimer = null;
	function hideSuggestions() {
		suggestionBox.hidden = true;
		suggestionBox.innerHTML = "";
	}

	function searchRecords(term) {
		const module = currentModule();
		if (!module || !term) {
			hideSuggestions();
			return;
		}
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: module.doctype,
				filters: [["name", "like", "%" + term + "%"]],
				fields: ["name"],
				limit_page_length: 10,
			},
			callback(response) {
				const rows = (response && response.message) || [];
				if (!rows.length) {
					hideSuggestions();
					return;
				}
				suggestionBox.innerHTML = rows
					.map((r) => `<div class="ucc-ask-suggestion" data-value="${esc(r.name)}">${esc(r.name)}</div>`)
					.join("");
				suggestionBox.hidden = false;
			},
			error: hideSuggestions,
		});
	}

	recordInput.addEventListener("input", () => {
		window.clearTimeout(searchTimer);
		searchTimer = window.setTimeout(() => searchRecords(recordInput.value.trim()), 250);
	});
	suggestionBox.addEventListener("click", (event) => {
		const option = event.target.closest("[data-value]");
		if (!option) return;
		recordInput.value = option.dataset.value;
		hideSuggestions();
		questionInput.focus();
	});
	document.addEventListener("click", (event) => {
		if (!suggestionBox.contains(event.target) && event.target !== recordInput) hideSuggestions();
	});
	moduleSelect.addEventListener("change", () => {
		recordInput.value = "";
		hideSuggestions();
	});

	// --- asking
	function ask() {
		if (state.busy) return;
		const module = currentModule();
		const record = recordInput.value.trim();
		const question = questionInput.value.trim();
		if (!module) return;
		if (!record) {
			setStatus("Select a record first.", "error");
			return;
		}
		if (!question) {
			setStatus("Enter a question first.", "error");
			return;
		}

		state.busy = true;
		submitButton.disabled = true;
		setStatus("Asking...");

		frappe.call({
			method: "ucc_intelligence.api.ask_ucc",
			args: { module: module.key, question: question, record: record },
			callback(response) {
				const message = response && response.message;
				if (message) {
					thread.insertAdjacentHTML("afterbegin", renderTurn(question, message, module));
					questionInput.value = "";
					setStatus("");
				} else {
					setStatus("The server returned no answer.", "error");
				}
			},
			error(error) {
				setStatus(window.UCCShared.errorText(error) || "The request failed.", "error");
			},
			always() {
				state.busy = false;
				submitButton.disabled = false;
			},
		});
	}

	submitButton.addEventListener("click", ask);
	questionInput.addEventListener("keydown", (event) => {
		if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) ask();
	});
}

// --- rendering -------------------------------------------------------------
// Three visually distinct zones, per the plan doc: what the AI said, the
// facts it was given, and where those came from. A reader must never have to
// guess which is which.

function renderTurn(question, message, module) {
	return (
		'<article class="ucc-ask-turn">'
		+ '<div class="ucc-ask-question-bubble">' + esc(question) + "</div>"
		+ renderAnswerZone(message, module)
		+ renderFactsZone(message)
		+ renderSourcesZone(message)
		+ "</article>"
	);
}

function renderAnswerZone(message, module) {
	// A blocked record renders the SAME notice Analytics uses for a blocked
	// source -- not a bespoke error box, and never a raw exception string.
	const blocked = (message.sources || []).find((s) => s.status === "permission_denied");
	if (blocked) {
		return window.UCCShared.permissionNoticeHtml({
			view: module ? module.label : "This answer",
			source: blocked.doctype,
			detail: blocked.message,
		});
	}

	const status = message.ai_status;
	if (status === "available" && message.answer) {
		return (
			'<div class="ucc-ask-zone ucc-ask-zone-ai">'
			+ '<div class="ucc-ask-zone-head">AI interpretation'
			+ (message.answer.model ? " &middot; " + esc(message.answer.model) : "")
			+ "</div>"
			+ '<div class="ucc-ask-zone-body"><div class="ucc-ask-answer-text">'
			+ esc(message.answer.text)
			+ "</div></div></div>"
		);
	}

	// Everything else -- AI disabled, unconfigured, errored, or its output
	// rejected by the citation guardrail -- says so plainly and leaves the
	// facts below standing on their own. That is the progressive-enhancement
	// contract, not a degraded failure state.
	const reasons = {
		disabled: "AI interpretation is turned off. The facts below come straight from live records.",
		unavailable: "AI interpretation is not configured. The facts below come straight from live records.",
		guardrail_blocked: "An AI answer was generated but referenced something not present in the retrieved facts, so it was withheld. The facts below are unaffected.",
		error: "AI interpretation could not be produced. The facts below come straight from live records.",
		not_found: "That record could not be found.",
	};
	const text = reasons[status] || "AI interpretation is unavailable. The facts below come straight from live records.";
	return (
		'<div class="ucc-ask-zone ucc-ask-zone-ai">'
		+ '<div class="ucc-ask-zone-head">AI interpretation unavailable</div>'
		+ '<div class="ucc-ask-zone-body"><div class="ucc-ask-ai-unavailable">'
		+ esc(text)
		+ (message.answer_error ? "<br>" + esc(message.answer_error) : "")
		+ "</div></div></div>"
	);
}

function humanise(key) {
	return String(key).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderFactValue(value) {
	if (value == null || value === "") return "&mdash;";
	if (Array.isArray(value)) {
		if (!value.length) return "&mdash;";
		if (typeof value[0] !== "object") return esc(value.join(", "));
		return esc(value.length + " record(s)");
	}
	if (typeof value === "object") return esc(JSON.stringify(value));
	if (typeof value === "boolean") return value ? "Yes" : "No";
	return esc(value);
}

function renderFactsZone(message) {
	const facts = message.facts || {};
	const groups = Object.keys(facts).filter((k) => facts[k] && facts[k].status === "available");
	if (!groups.length) return "";

	const body = groups
		.map((toolName) => {
			const group = facts[toolName];
			const rows = Object.keys(group)
				.filter((k) => k !== "status" && k !== "note")
				.map((k) => "<tr><th>" + esc(humanise(k)) + "</th><td>" + renderFactValue(group[k]) + "</td></tr>")
				.join("");
			return (
				'<div class="ucc-ask-fact-group"><h4>' + esc(humanise(toolName)) + "</h4>"
				+ '<table class="ucc-ask-fact-table">' + rows + "</table>"
				+ (group.note ? '<p class="ucc-card-description">' + esc(group.note) + "</p>" : "")
				+ "</div>"
			);
		})
		.join("");

	return (
		'<div class="ucc-ask-zone ucc-ask-zone-facts">'
		+ '<div class="ucc-ask-zone-head">Facts from live records</div>'
		+ '<div class="ucc-ask-zone-body">' + body + "</div></div>"
	);
}

function renderSourcesZone(message) {
	const sources = (message.sources || []).filter((s) => s.status === "available" && s.record);
	if (!sources.length) return "";
	const links = sources
		.map((s) => {
			const route = window.UCCShared.doctypeRoute(s.doctype) + "/" + encodeURIComponent(s.record);
			return '<a class="ucc-ask-source" href="' + esc(route) + '" target="_blank" rel="noopener">'
				+ esc(s.doctype) + ": " + esc(s.record) + " &#8599;</a>";
		})
		.join("");
	return (
		'<div class="ucc-ask-zone">'
		+ '<div class="ucc-ask-zone-head">Sources</div>'
		+ '<div class="ucc-ask-zone-body">' + links + "</div></div>"
	);
}
