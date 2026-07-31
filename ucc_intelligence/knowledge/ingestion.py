"""Getting a document from "someone has a file" to "retrieval can cite it"
(CLAUDE.md Phase 9).

THE FLOW
    register  -> a UCC Knowledge Source record: title, type, version,
                 effective date, classification, who may read it
    extract   -> text out of whatever was attached
    index     -> retrieval.index_source() splits into sections and stores
                 UCC Knowledge Chunk rows with headings for citation
    retrieve  -> retrieval.search(), permission-filtered, with citations

EXTRACTION SCOPE, AND WHY IT IS NARROW
Plain text and Markdown only. PDF and DOCX extraction needs a new dependency
(pdfminer, python-docx), which is a decision rather than a line of code --
it adds an unvetted parser to a system that reads institutional documents.
An unsupported file type is REFUSED with a clear message, never partially
extracted: half a policy indexed as if it were whole is worse than no policy
indexed at all, because retrieval would confidently cite the half it has.

Anything an admin can paste, they can index today. Anything in a PDF waits
for that decision.
"""

import frappe

from ucc_intelligence.knowledge import retrieval

SUPPORTED_EXTENSIONS = (".txt", ".md", ".markdown")
UNSUPPORTED_NOTE = (
	"Only plain text and Markdown can be extracted today. PDF and DOCX need a "
	"document-parsing dependency that has not been approved. Paste the text into "
	"the source record, or convert the file first."
)


def extract_text(file_url):
	"""Text out of an attached Frappe File. Returns (text, error)."""
	if not file_url:
		return "", "No file is attached to this source."

	name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not name:
		return "", "The attached file could not be found."

	file_doc = frappe.get_doc("File", name)
	lowered = (file_doc.file_name or "").lower()
	if not lowered.endswith(SUPPORTED_EXTENSIONS):
		return "", "%s: %s" % (file_doc.file_name or "file", UNSUPPORTED_NOTE)

	try:
		content = file_doc.get_content()
	except Exception as error:
		return "", "Could not read the file: %s" % frappe.utils.cstr(error)

	if isinstance(content, bytes):
		try:
			content = content.decode("utf-8")
		except UnicodeDecodeError:
			return "", "The file is not valid UTF-8 text."
	return content, ""


def register_source(title, source_type, text=None, attached_file=None, **fields):
	"""Create a knowledge source and index it in one step.

	Text may be supplied directly (paste) or come from an attachment. Direct
	text wins if both are given -- an admin who pasted content meant that
	content.
	"""
	doc = frappe.get_doc({
		"doctype": "UCC Knowledge Source",
		"title": title,
		"source_type": source_type,
		"attached_file": attached_file,
		"document_version": fields.get("document_version"),
		"effective_date": fields.get("effective_date"),
		"review_date": fields.get("review_date"),
		"classification": fields.get("classification") or "Internal",
		"permission_role": fields.get("permission_role"),
		"owner_department": fields.get("owner_department"),
		"is_active": 1,
		"sync_status": "Not Indexed",
	}).insert()

	result = index_source(doc.name, text=text)
	return dict(result, source=doc.name)


def index_source(source_name, text=None):
	"""(Re)index one source. Records WHY on failure rather than leaving the
	source stuck at 'Not Indexed' with no explanation."""
	source = frappe.get_doc("UCC Knowledge Source", source_name)

	if text is None:
		text, error = extract_text(source.attached_file)
		if error:
			source.sync_status = "Failed"
			source.save(ignore_permissions=True)
			return {"ok": False, "indexed": False, "message": error}

	if not (text or "").strip():
		source.sync_status = "Failed"
		source.save(ignore_permissions=True)
		return {"ok": False, "indexed": False, "message": "The document is empty; nothing to index."}

	result = retrieval.index_source(source_name, text)
	return {"ok": True, "indexed": True, "sections": result["sections"]}


def supersede(old_source_name, new_source_name):
	"""Retire a document in favour of its replacement.

	Both halves matter: the old source is marked superseded (retrieval then
	excludes it structurally, so it can never be quoted as current), and its
	chunks are marked not-current so nothing stale survives in the index.
	"""
	old = frappe.get_doc("UCC Knowledge Source", old_source_name)
	old.superseded_by = new_source_name
	old.is_active = 0
	old.save()

	for chunk in frappe.get_all("UCC Knowledge Chunk", filters={"source": old_source_name},
			pluck="name", limit_page_length=0, ignore_permissions=True):
		frappe.db.set_value("UCC Knowledge Chunk", chunk, "is_current", 0)

	return {"ok": True, "superseded": old_source_name, "by": new_source_name}


def reindex_stale():
	"""Re-index every source whose stored checksum no longer matches its file.

	Scheduler-friendly. A source with no attachment is skipped rather than
	failed: its text was pasted, so there is no file to have drifted from.
	"""
	checked = reindexed = skipped = 0
	for row in frappe.get_all("UCC Knowledge Source", filters={"is_active": 1},
			fields=["name", "attached_file"], limit_page_length=0):
		if not row["attached_file"]:
			skipped += 1
			continue
		checked += 1
		text, error = extract_text(row["attached_file"])
		if error:
			continue
		if retrieval.is_stale(row["name"], text):
			index_source(row["name"], text=text)
			reindexed += 1
	return {"ok": True, "checked": checked, "reindexed": reindexed, "skipped_no_file": skipped}
