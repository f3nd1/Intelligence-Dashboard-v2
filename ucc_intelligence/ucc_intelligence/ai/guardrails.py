"""Output validation for Ask UCC's AI-generated explanations
(docs/architecture/ask-ucc-phase-plan.md §2.1 step 7): before an answer is
ever rendered, confirm it doesn't reference a record the supplied facts
never contained. This is the concrete, checked implementation of
CLAUDE.md Phase 8's "AI must not fabricate source links" -- enforced in
code, not just instructed in the prompt.
"""

import re

# Frappe's hash-based autoname (used by Insights Query v3 records all
# session, and by every DocType in this build too) produces short
# lowercase alphanumeric tokens -- flag anything shaped like one so it can
# be checked against what was actually supplied to the model.
RECORD_TOKEN_PATTERN = re.compile(r"\b[a-z0-9]{8,12}\b")
MAX_ANSWER_LENGTH = 4000


def extract_record_like_tokens(text):
	return set(RECORD_TOKEN_PATTERN.findall((text or "").lower()))


def validate(answer_text, known_record_names):
	"""Returns (ok, reason). known_record_names is every record identifier
	that was actually present in the facts supplied to the model -- the
	only ones it's allowed to reference. Deliberately conservative: a
	handful of false positives (a real word that happens to match the
	token shape) cost a re-generation; one fabricated citation reaching a
	user unflagged is the failure mode this exists to prevent."""
	if not answer_text or not answer_text.strip():
		return False, "Empty response from the AI provider."
	if len(answer_text) > MAX_ANSWER_LENGTH:
		return False, "Response exceeded the maximum expected length."

	known = {str(name).lower() for name in known_record_names if name}
	mentioned = extract_record_like_tokens(answer_text)
	unverified = mentioned - known
	# Only flag tokens that mix letters and digits -- closer to how a real
	# Frappe hash-autoname actually looks, so an ordinary short lowercase
	# English word (all letters) sharing the length range isn't flagged.
	suspicious = sorted(token for token in unverified if any(char.isdigit() for char in token))
	if suspicious:
		return False, "Response references identifier(s) not present in the supplied facts: " + ", ".join(suspicious)

	return True, None
