# Copyright (c) 2026, United Ceres College Pte Ltd
# For license information, please see license.txt

# Standalone DocType, not a child table of UCC AI Conversation -- a decision
# CLAUDE.md §7.3 explicitly says not to make silently, so recorded here:
# a conversation's message count is unbounded (every turn adds one), and a
# Frappe child table loads in full with its parent every time the parent is
# fetched, which doesn't scale to "show the last 20 messages" the way a
# direct, filtered, paginated query against a standalone DocType does. It
# also allows usage-style queries ("messages this month") without loading
# whole conversations.

from frappe.model.document import Document


class UCCAIMessage(Document):
	pass
