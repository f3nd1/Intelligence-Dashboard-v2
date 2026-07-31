# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document

# A provider API key must never be storable on this DocType. The key belongs
# in site_config.json (ucc_intelligence_ai_api_key) -- ai/client.py reads it
# from there and from nowhere else -- because a DocType field is readable by
# anyone with read access to the form, survives in the document's version
# history, and appears in backups and exports.
#
# This guard exists because the AI Provider field was a plain Data field and a
# real key was pasted into it. Making that one field a Select fixes that one
# field; this makes the whole DocType refuse a key, including any field added
# later by someone who did not read this file.
#
# ponytail: matches the `sk-` prefix family (OpenAI, incl. sk-proj-, and
# Anthropic's sk-ant-), which is what UCC would plausibly paste. It is a
# guard-rail against an accident, not a defence against someone determined to
# store a secret in a text box -- a base64 blob with no recognisable prefix
# would pass. Widen the pattern if another provider is ever approved.
API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-]{16,}", re.IGNORECASE)


def looks_like_api_key(value):
	return bool(value) and bool(API_KEY_PATTERN.search(str(value)))


class UCCIntelligenceSettings(Document):
	def validate(self):
		self.reject_api_key_values()
		if self.default_temperature is not None:
			self.default_temperature = max(0.0, min(2.0, self.default_temperature))

	def reject_api_key_values(self):
		"""Refuse to save if any text field holds something shaped like an API
		key. The message names the FIELD only -- echoing the value back would
		write the secret into the error log and the user's screen, which is
		the thing being prevented."""
		for field in self.meta.fields:
			if field.fieldtype not in ("Data", "Select", "Small Text", "Text", "Long Text", "Code", "Password"):
				continue
			if looks_like_api_key(self.get(field.fieldname)):
				frappe.throw(
					frappe._(
						"{0} looks like an API key. API keys are never stored on this form -- "
						"put the key in site_config.json as ucc_intelligence_ai_api_key. "
						"Clear this field and save again."
					).format(frappe._(field.label or field.fieldname)),
					title=frappe._("API key must not be stored here"),
				)
