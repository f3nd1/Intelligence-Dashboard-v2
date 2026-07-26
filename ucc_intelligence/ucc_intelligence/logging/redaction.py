"""Minimum redaction helpers for audit logging.

CLAUDE.md §12.2 (personal data minimisation) and §12.4 (audit trail): log
metadata, not full content. This module has one job at Phase 2: keep a
failed query's exception text from carrying secrets or unbounded content
into the log. It is intentionally small -- extend it if a later phase
(AI usage logging, Phase 8) needs to redact richer content, not before.
"""

import re

MAX_ERROR_LENGTH = 300

_SECRET_PATTERNS = [
	re.compile(r"Bearer\s+\S+", re.IGNORECASE),
	re.compile(r"api[_-]?key\s*[=:]\s*\S+", re.IGNORECASE),
	re.compile(r"password\s*[=:]\s*\S+", re.IGNORECASE),
]


def redact_error_text(value):
	"""Truncate and strip secret-shaped substrings from an error message."""
	text = str(value or "")
	for pattern in _SECRET_PATTERNS:
		text = pattern.sub("[redacted]", text)
	if len(text) > MAX_ERROR_LENGTH:
		text = text[:MAX_ERROR_LENGTH] + "...[truncated]"
	return text
