#!/usr/bin/env python3
"""Self-check for document knowledge (CLAUDE.md Phase 9 groundwork).

The two properties worth proving are not "search returns something":

1. A SUPERSEDED or not-yet-effective document can never be quoted as
   current. CLAUDE.md §9 makes this a source-priority requirement, and it
   is the one that matters for compliance answers -- an answer citing a
   retired policy is worse than no answer.
2. A RESTRICTED document is never retrieved for a user without the role,
   no matter how well it matches. Retrieval must not become a way to read
   documents you cannot open.

Both are enforced structurally (the document is not a candidate at all)
rather than by ranking, so both are tested by asserting absence.

    python3 tools/test_ucc_intelligence_knowledge.py
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
checks = []


def report(ok, message):
	print(("PASS" if ok else "FAIL") + ": " + message)
	checks.append(bool(ok))
	return ok


sys.path.insert(0, str(ROOT / "ucc_intelligence"))


class State:
	sources = {}
	chunks = {}
	roles = ["All"]
	counter = 0


class FakeDoc(dict):
	def __init__(self, values):
		super().__init__(values)
		self.__dict__ = self

	def __getattr__(self, name):
		if name.startswith("__"):
			raise AttributeError(name)
		return None

	def insert(self, ignore_permissions=False):
		State.counter += 1
		self["name"] = self.get("name") or "CHUNK-%04d" % State.counter
		State.chunks[self["name"]] = self
		return self

	def save(self, ignore_permissions=False):
		if self["doctype"] == "UCC Knowledge Source":
			State.sources[self["name"]] = self
		return self


def _get_doc(arg, name=None):
	if isinstance(arg, dict):
		return FakeDoc(dict(arg))
	if arg == "UCC Knowledge Source":
		return State.sources[name]
	return State.chunks[name]


def _get_all(doctype, filters=None, fields=None, limit_page_length=None,
		ignore_permissions=False, order_by=None, pluck=None):
	if doctype == "UCC Knowledge Source":
		rows = [dict(r) for r in State.sources.values()]
		if filters and "is_active" in filters:
			rows = [r for r in rows if r.get("is_active")]
	else:
		rows = [dict(r) for r in State.chunks.values()]
		if filters:
			if "source" in filters:
				# Real frappe.get_all takes both {"f": value} and
				# {"f": ["in", [...]]}; the code under test uses both, so the
				# fake must too or a genuine call silently matches nothing.
				condition = filters["source"]
				allowed = condition[1] if isinstance(condition, (list, tuple)) else [condition]
				rows = [r for r in rows if r.get("source") in allowed]
			if "is_current" in filters:
				rows = [r for r in rows if r.get("is_current")]
	if pluck:
		return [r[pluck] for r in rows]
	return rows


frappe_stub = types.ModuleType("frappe")
frappe_stub.get_doc = _get_doc
frappe_stub.get_all = _get_all
frappe_stub.get_list = _get_all
frappe_stub.get_roles = lambda user=None: list(State.roles)
frappe_stub.session = types.SimpleNamespace(user="staff@ucc")
frappe_stub.delete_doc = lambda dt, name, **kw: State.chunks.pop(name, None)
frappe_stub._ = lambda text, *a, **k: text
utils = types.ModuleType("frappe.utils")
utils.now = staticmethod(lambda: "2026-07-31 04:00:00")
utils.today = staticmethod(lambda: "2026-07-31")
utils.cint = lambda v: int(v) if str(v or "").strip().lstrip("-").isdigit() else 0
utils.cstr = lambda v: "" if v is None else str(v)
frappe_stub.utils = utils
sys.modules["frappe"] = frappe_stub
sys.modules["frappe.utils"] = utils

from ucc_intelligence.knowledge import retrieval  # noqa: E402

# ============================================================
# Chunking: sections, not a fixed window
# ============================================================
DOC = """# Refund Policy

Students may request a refund within 14 days of course commencement.

# Withdrawal Procedure

A withdrawal must be submitted in writing to Student Services.
The Registrar confirms the withdrawal within five working days.
"""
sections = retrieval.split_sections(DOC)
report(len(sections) == 2, "a document splits on its headings, not on a character count")
report(sections[0]["heading"] == "Refund Policy", "the heading is captured for citation")
report("14 days" in sections[0]["content"], "the section keeps its own body")
report("Registrar" in sections[1]["content"] and "Registrar" not in sections[0]["content"],
	"sections do not bleed into each other")

long_body = "\n\n".join(["Paragraph %d. %s" % (i, "word " * 60) for i in range(20)])
packed = retrieval.split_sections("# Big Section\n\n" + long_body)
report(len(packed) > 1, "an oversized section is packed down -- a citation to a 40-page section is not a citation")
report(all(len(p["content"]) <= retrieval.TARGET_CHUNK_CHARS * 1.6 for p in packed),
	"packed sections stay near the target size")
report(all(p["heading"] == "Big Section" for p in packed),
	"packed pieces keep the heading they came from, so citations stay accurate")
report(retrieval.split_sections("") == [], "an empty document produces no sections, not one empty one")

# ============================================================
# Indexing and stale detection
# ============================================================
def add_source(name, title, **kwargs):
	State.sources[name] = FakeDoc(dict({
		"doctype": "UCC Knowledge Source", "name": name, "title": title,
		"is_active": 1, "superseded_by": None, "effective_date": None,
		"permission_role": None, "document_version": None,
	}, **kwargs))
	return State.sources[name]


add_source("KS-1", "Refund Policy", document_version="3")
result = retrieval.index_source("KS-1", DOC)
report(result["sections"] == 2, "indexing stores one chunk per section")
report(State.sources["KS-1"]["sync_status"] == "Indexed", "the source records that it is indexed")
report(bool(State.sources["KS-1"]["content_checksum"]), "a checksum of the indexed text is stored")
report(State.sources["KS-1"]["chunk_count"] == 2, "the section count is recorded")

report(retrieval.is_stale("KS-1", DOC) is False, "an unchanged document is not stale")
report(retrieval.is_stale("KS-1", DOC + "\n# New Section\n\nMore text.") is True,
	"an EDITED document is detected as stale -- an index that drifted answers with unapproved wording")

before = len(State.chunks)
retrieval.index_source("KS-1", DOC)
report(len(State.chunks) == before,
	"REINDEX: chunks are replaced, not appended -- orphans would let retired wording keep surfacing")

# ============================================================
# Retrieval, citations, and honest empties
# ============================================================
found = retrieval.search("refund within 14 days")
report(found["results"], "a matching question returns sections")
report(found["results"][0]["heading"] == "Refund Policy",
	"the best match is the section actually about refunds")
report("Refund Policy" in found["results"][0]["citation"] and "v3" in found["results"][0]["citation"],
	"the citation names the document AND its version")
report("Refund Policy" in found["results"][0]["citation"].split(" · ")[-1]
	or found["results"][0]["heading"] in found["results"][0]["citation"],
	"the citation names the exact section, not just the document")

report(retrieval.search("quantum chromodynamics")["results"] == [],
	"a question with no match returns nothing rather than the closest unrelated text")
report("note" in retrieval.search("quantum chromodynamics"),
	"...and says so, per CLAUDE.md §14.3 -- never invent a policy answer")
report(retrieval.search("the and of")["results"] == [],
	"a query of only stopwords returns nothing rather than everything")

# heading matches must outrank passing body mentions
add_source("KS-2", "Student Handbook")
retrieval.index_source("KS-2", "# Introduction\n\nThis handbook mentions refund arrangements in passing.\n")
ranked = retrieval.search("refund")
report(ranked["results"][0]["document"] == "Refund Policy",
	"a section TITLED for the query outranks a passing mention elsewhere")

# ============================================================
# THE source-priority property: superseded is never current
# ============================================================
add_source("KS-3", "Refund Policy (2019)", document_version="2")
retrieval.index_source("KS-3", "# Refund Policy\n\nStudents may request a refund within 30 days.\n")
report(any(r["source"] == "KS-3" for r in retrieval.search("refund within days")["results"]),
	"precondition: the old policy IS findable before it is superseded")

State.sources["KS-3"]["superseded_by"] = "KS-1"
after = retrieval.search("refund within days")
report(not any(r["source"] == "KS-3" for r in after["results"]),
	"SOURCE PRIORITY: a SUPERSEDED policy is never returned -- not ranked lower, absent")
report(any(r["source"] == "KS-1" for r in after["results"]),
	"...while the current version still answers")

State.sources["KS-3"]["superseded_by"] = None
State.sources["KS-3"]["is_active"] = 0
report(not any(r["source"] == "KS-3" for r in retrieval.search("refund within days")["results"]),
	"SOURCE PRIORITY: an INACTIVE document is never returned")

State.sources["KS-3"]["is_active"] = 1
State.sources["KS-3"]["effective_date"] = "2099-01-01"
report(not any(r["source"] == "KS-3" for r in retrieval.search("refund within days")["results"]),
	"SOURCE PRIORITY: a policy that is not yet effective is never returned as current")
State.sources["KS-3"]["effective_date"] = "2020-01-01"
report(any(r["source"] == "KS-3" for r in retrieval.search("refund within days")["results"]),
	"...and a past effective date is fine")
State.sources["KS-3"]["is_active"] = 0

# ============================================================
# THE permission property: restricted content stays restricted
# ============================================================
add_source("KS-4", "Staff Disciplinary Procedure", permission_role="HR Manager")
retrieval.index_source("KS-4", "# Disciplinary Procedure\n\nA disciplinary hearing follows a written allegation.\n")

State.roles = ["All", "Academic Staff"]
restricted = retrieval.search("disciplinary hearing allegation")
report(not any(r["source"] == "KS-4" for r in restricted["results"]),
	"PERMISSION: a role-restricted document is NOT retrieved for a user without the role")
report(not any("disciplinary hearing" in (r["content"] or "").lower() for r in restricted["results"]),
	"PERMISSION: and its CONTENT does not leak through some other result either")

State.roles = ["All", "HR Manager"]
permitted = retrieval.search("disciplinary hearing allegation")
report(any(r["source"] == "KS-4" for r in permitted["results"]),
	"PERMISSION: the same query DOES return it for a user who holds the role")

State.roles = ["All"]
report(retrieval.search("refund")["results"], "an unrestricted document is still readable by an ordinary user")

# ============================================================
# No external calls -- this is the §19-blocker boundary
# ============================================================
source_text = (ROOT / "ucc_intelligence/ucc_intelligence/knowledge/retrieval.py").read_text(encoding="utf-8")
for forbidden in ("requests.", "make_post_request", "make_get_request", "openai", "embedding", "http://", "https://"):
	report(forbidden not in source_text.lower().replace("embeddings would mean", "").replace("embeddings provider", ""),
		"NO EXTERNAL CALLS: retrieval.py contains no %r -- no document content leaves the estate" % forbidden)

passed = all(checks)
print()
print(("PASS" if passed else "FAIL") + ": %d/%d checks" % (sum(checks), len(checks)))
raise SystemExit(0 if passed else 1)
