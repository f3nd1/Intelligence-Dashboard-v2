"""Shared low-level value helpers used by the per-criterion analytics engines.

Extracted from `server-scripts/UCC Analytics - Criterion 1.py` (verbatim,
modulo the tabs-not-spaces indent convention already established in
`contracts.py`), and hash-verified against all seven criterion scripts
before being pulled out here -- not assumed shared:

- `lower_text` and `is_truthy` are byte-identical across all seven scripts.
- `clean_text` is byte-identical in six of seven (1, 2, 3, 5, 6, 7);
  Criterion 4's own copy differs. This module's version matches the
  six-of-seven majority, which Criterion 1 (the first criterion ported)
  belongs to. Re-check against Criterion 4's actual divergence when Criterion
  4 is ported, per the Phase 4 plan's Decision C -- don't assume it can just
  swap over to this shared version without checking.

Not the same function as `analytics.contracts.is_permission_error` (which
lives in contracts.py already, from Phase 2, and is reused directly rather
than re-derived here).
"""


def clean_text(value):
	if value is None:
		return ""
	return str(value).strip()

def lower_text(value):
	return clean_text(value).lower()

def is_truthy(value):
	if value in [None, "", 0, "0", False]:
		return False
	if lower_text(value) in ["false", "no", "unchecked", "none", "null"]:
		return False
	return True
