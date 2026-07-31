"""Deterministic, permission-aware, citation-carrying document retrieval
(CLAUDE.md Phase 9 groundwork).

DELIBERATELY NOT SEMANTIC. There is no embeddings provider here, and that
is a decision rather than an omission: embeddings would mean sending UCC
policy and course content to an external service, which is a CLAUDE.md §19
item (approved provider account, and whether institutional data may leave
the estate) that has not been decided. Keyword retrieval needs no external
account, no new data-sharing agreement, and no vector store -- and it is
reversible: `search()`'s contract (a ranked list of chunks with citations)
does not change when a semantic scorer is added behind it.

What this DOES implement from CLAUDE.md §9's "minimum knowledge features":
source registration, version handling, effective/superseded dates,
section-level retrieval, permission filtering, citations, sync status and
stale-index detection. What it does not: extraction from PDF/DOCX (a new
dependency and a separate decision -- ingestion currently takes text that
is already text), and any external index.

Source priority (CLAUDE.md §9) is enforced structurally rather than by
scoring: a superseded or inactive document is not a candidate at all, so a
retired policy cannot be presented as current no matter how well its
wording matches.
"""

import hashlib
import re

import frappe

WORD = re.compile(r"[a-z0-9]+")
# Words too common to discriminate. Kept deliberately short -- an aggressive
# stop list silently drops real query terms ("act", "no", "all" appear in
# policy titles), and a term that matches everything simply scores everything
# equally, which is harmless here.
STOPWORDS = {"the", "a", "an", "of", "and", "or", "to", "in", "for", "is", "are", "on", "at", "by", "with", "that", "this", "it", "as", "be"}

MAX_RESULTS = 20
# A section long enough to be its own answer, short enough to cite precisely.
TARGET_CHUNK_CHARS = 1200
HEADING_LINE = re.compile(r"^\s{0,3}(#{1,6}\s+.+|[A-Z0-9][^\n]{0,80})\s*$")


def tokenise(text):
	return [w for w in WORD.findall((text or "").lower()) if w not in STOPWORDS and len(w) > 1]


def checksum(text):
	return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def split_sections(text):
	"""Split on markdown-style headings, falling back to paragraph packing.

	Section-level retrieval is the point (CLAUDE.md §9: "retain
	page/heading/source metadata"), so a heading is preferred over a fixed
	character window wherever the document has them.

	ponytail: headings-then-paragraphs, no layout analysis. Good enough for
	the markdown/plain-text policies this indexes today; a PDF with real
	page structure will want page numbers, which is where that goes.
	"""
	lines = (text or "").splitlines()
	sections = []
	heading = ""
	buffer = []

	def flush():
		body = "\n".join(buffer).strip()
		if body:
			sections.append({"heading": heading, "content": body})

	for line in lines:
		stripped = line.strip()
		is_heading = bool(stripped) and (
			stripped.startswith("#")
			or (len(stripped) <= 80 and stripped == stripped.upper() and any(c.isalpha() for c in stripped))
		)
		if is_heading:
			flush()
			buffer = []
			heading = stripped.lstrip("# ").strip()
			continue
		buffer.append(line)
	flush()

	if not sections:
		return pack_paragraphs(text, heading="")

	# A section that is still enormous gets packed down; a citation to a
	# 40-page "Introduction" is not a citation.
	output = []
	for section in sections:
		if len(section["content"]) <= TARGET_CHUNK_CHARS:
			output.append(section)
		else:
			output.extend(pack_paragraphs(section["content"], section["heading"]))
	return output


def pack_paragraphs(text, heading):
	chunks = []
	current = []
	size = 0
	for paragraph in re.split(r"\n\s*\n", text or ""):
		paragraph = paragraph.strip()
		if not paragraph:
			continue
		if size and size + len(paragraph) > TARGET_CHUNK_CHARS:
			chunks.append({"heading": heading, "content": "\n\n".join(current)})
			current, size = [], 0
		current.append(paragraph)
		size += len(paragraph)
	if current:
		chunks.append({"heading": heading, "content": "\n\n".join(current)})
	return chunks


def index_source(source_name, text):
	"""(Re)index one document. Replaces its chunks wholesale rather than
	diffing -- a policy is republished, not edited in place, and a partial
	reindex that leaves orphan chunks would let retired wording keep
	surfacing.

	ignore_permissions is used for the chunk writes: chunks are derived data
	the system owns, and the caller has already been permission-checked on
	the source. Retrieval is where permissions are enforced, and it is
	enforced there per-chunk.
	"""
	source = frappe.get_doc("UCC Knowledge Source", source_name)

	for existing in frappe.get_all("UCC Knowledge Chunk", filters={"source": source_name},
			pluck="name", limit_page_length=0, ignore_permissions=True):
		frappe.delete_doc("UCC Knowledge Chunk", existing, ignore_permissions=True, force=True)

	sections = split_sections(text)
	for index, section in enumerate(sections):
		frappe.get_doc({
			"doctype": "UCC Knowledge Chunk",
			"source": source_name,
			"section_index": index,
			"heading": section["heading"][:140],
			"content": section["content"],
			"source_title": source.title,
			"permission_role": source.permission_role,
			"is_current": 1,
		}).insert(ignore_permissions=True)

	source.content_checksum = checksum(text)
	source.chunk_count = len(sections)
	source.sync_status = "Indexed"
	source.last_indexed_at = frappe.utils.now()
	source.save(ignore_permissions=True)
	return {"ok": True, "source": source_name, "sections": len(sections)}


def is_stale(source_name, text):
	"""Whether the stored index still matches the document it came from.
	CLAUDE.md §9 requires stale-index detection explicitly -- an index that
	has quietly drifted from its source is worse than no index, because it
	answers confidently with wording nobody approved."""
	source = frappe.get_doc("UCC Knowledge Source", source_name)
	return source.content_checksum != checksum(text)


def current_source_names(user=None):
	"""Documents eligible to be quoted as current: active, not superseded,
	effective by now, and permitted to this user.

	Structural, not scored. A retired policy is not a low-ranked result --
	it is not a result.
	"""
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	today = frappe.utils.today()

	rows = frappe.get_all(
		"UCC Knowledge Source",
		filters={"is_active": 1},
		fields=["name", "title", "superseded_by", "effective_date", "permission_role", "document_version"],
		limit_page_length=0,
	)
	eligible = {}
	for row in rows:
		if row["superseded_by"]:
			continue
		if row["effective_date"] and str(row["effective_date"]) > str(today):
			continue
		if row["permission_role"] and row["permission_role"] not in roles:
			continue
		eligible[row["name"]] = row
	return eligible


def score(query_tokens, chunk):
	"""Term overlap, weighted so a heading match counts for more than a body
	match -- a section titled "Refund Policy" is a better answer to "refund
	policy" than a passing mention in an appendix.

	ponytail: overlap counting, not BM25. With a few hundred policy sections
	the ranking difference is not worth the length normalisation tuning; if
	the corpus grows enough for long documents to crowd out short ones, BM25
	is the drop-in replacement and this function is the only thing it
	touches.
	"""
	heading_tokens = set(tokenise(chunk.get("heading")))
	body_tokens = tokenise(chunk.get("content"))
	body_set = set(body_tokens)

	matched = 0
	total = 0
	for token in query_tokens:
		if token in heading_tokens:
			total += 3
			matched += 1
		if token in body_set:
			total += 1 + min(body_tokens.count(token), 5) * 0.2
			matched += 1
	if not matched:
		return 0
	# Require more than a single incidental term when the query is specific.
	coverage = len({t for t in query_tokens if t in heading_tokens or t in body_set}) / len(set(query_tokens))
	return total * coverage


def search(query, limit=5, user=None):
	"""Ranked sections with citations, or an honest empty result.

	Never fabricates: if nothing matches, that is what comes back. CLAUDE.md
	§14.3 -- "Do not invent a policy answer, show source search unavailable."
	"""
	query_tokens = tokenise(query)
	if not query_tokens:
		return {"ok": True, "results": [], "note": "No searchable terms in the question."}

	eligible = current_source_names(user=user)
	if not eligible:
		return {"ok": True, "results": [], "note": "No current knowledge sources are available to your account."}

	limit = max(1, min(MAX_RESULTS, frappe.utils.cint(limit) or 5))
	chunks = frappe.get_all(
		"UCC Knowledge Chunk",
		filters={"source": ["in", list(eligible)], "is_current": 1},
		fields=["name", "source", "source_title", "heading", "content", "section_index"],
		limit_page_length=0,
	)

	scored = []
	for chunk in chunks:
		value = score(query_tokens, chunk)
		if value > 0:
			scored.append((value, chunk))
	scored.sort(key=lambda pair: (-pair[0], pair[1]["source_title"] or "", pair[1]["section_index"] or 0))

	results = []
	for value, chunk in scored[:limit]:
		source = eligible[chunk["source"]]
		results.append({
			"source": chunk["source"],
			"citation": citation_for(source, chunk),
			"document": chunk["source_title"],
			"version": source.get("document_version"),
			"heading": chunk["heading"],
			"section_index": chunk["section_index"],
			"content": chunk["content"],
			"score": round(value, 3),
		})

	if not results:
		return {"ok": True, "results": [], "note": "No current document section matches that question."}
	return {"ok": True, "results": results}


def citation_for(source, chunk):
	"""Document, version and section -- never the document alone. An answer
	a reader cannot check back to an exact section is not sourced."""
	parts = [source.get("title") or chunk.get("source_title") or "Untitled document"]
	if source.get("document_version"):
		parts.append("v%s" % source["document_version"])
	if chunk.get("heading"):
		parts.append(chunk["heading"])
	else:
		parts.append("section %s" % ((chunk.get("section_index") or 0) + 1))
	return " · ".join(parts)
