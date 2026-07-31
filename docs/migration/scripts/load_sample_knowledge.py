"""Load the SAMPLE knowledge documents so the whole document pipeline can be
exercised on a real bench.

Every document loaded here is INVENTED (docs/samples/knowledge/). They are
for testing register -> extract -> chunk -> index -> retrieve -> cite, not a
starting corpus. Each announces SAMPLE on its first line, so a chunk
retrieved from one is self-identifying even quoted out of context.

RUN
    bench --site <site> console
    >>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/load_sample_knowledge.py").read(), globals())

  globals() matters -- without it top-level defs land in locals.

REMOVE
    >>> DELETE_INSTEAD = True
    >>> exec(open(".../load_sample_knowledge.py").read(), globals())
"""

import os

import frappe

from ucc_intelligence.knowledge import ingestion, retrieval

SAMPLE_TITLE_PREFIX = "SAMPLE "
SAMPLES = [
	("SAMPLE Refund Policy", "Policy", "SAMPLE-refund-policy.md", "1", "refund within 14 days"),
	("SAMPLE Attendance Procedure", "Procedure", "SAMPLE-attendance-procedure.md", "1", "attendance below the threshold"),
]


def samples_dir():
	"""docs/samples/knowledge, relative to the installed app."""
	import ucc_intelligence
	app_root = os.path.dirname(os.path.dirname(os.path.abspath(ucc_intelligence.__file__)))
	for candidate in (
		os.path.join(app_root, "..", "docs", "samples", "knowledge"),
		os.path.join(app_root, "docs", "samples", "knowledge"),
	):
		if os.path.isdir(candidate):
			return os.path.abspath(candidate)
	return None


def delete_samples():
	removed = 0
	for row in frappe.get_all("UCC Knowledge Source", fields=["name", "title"], limit_page_length=0):
		if str(row["title"] or "").startswith(SAMPLE_TITLE_PREFIX):
			for chunk in frappe.get_all("UCC Knowledge Chunk", filters={"source": row["name"]},
					pluck="name", limit_page_length=0):
				frappe.delete_doc("UCC Knowledge Chunk", chunk, ignore_permissions=True, force=True)
			frappe.delete_doc("UCC Knowledge Source", row["name"], ignore_permissions=True, force=True)
			removed += 1
	frappe.db.commit()
	print("Removed %d SAMPLE knowledge source(s) and their chunks." % removed)


def load():
	directory = samples_dir()
	if not directory:
		print("STOP -- could not locate docs/samples/knowledge next to the installed app.")
		return

	print("Loading samples from %s" % directory)
	loaded = []
	for title, source_type, filename, version, probe in SAMPLES:
		path = os.path.join(directory, filename)
		if not os.path.isfile(path):
			print("   MISSING %s" % filename)
			continue
		if frappe.db.get_value("UCC Knowledge Source", {"title": title}, "name"):
			print("   exists  %s" % title)
			loaded.append((title, probe))
			continue
		with open(path, "r", encoding="utf-8") as handle:
			text = handle.read()
		result = ingestion.register_source(
			title, source_type, text=text, document_version=version,
			effective_date="2026-01-01", classification="Internal")
		print("   %-32s %s (%s sections)" % (title, "indexed" if result["indexed"] else "FAILED",
			result.get("sections", 0)))
		loaded.append((title, probe))
	frappe.db.commit()

	print("\n--- retrieving each one back, with citations ---")
	for title, probe in loaded:
		found = retrieval.search(probe, limit=2)
		if not found["results"]:
			print("   %-32s NO RESULT for %r -- pipeline broken" % (title, probe))
			continue
		top = found["results"][0]
		print("   %-32s -> %s" % (title, top["citation"]))
		print("      %s" % top["content"][:120].replace("\n", " "))

	print("\nEnable Document Knowledge on UCC Intelligence Settings to expose this")
	print("through ucc_intelligence.api.search_knowledge; retrieval above is direct.")


DELETE_INSTEAD = globals().get("DELETE_INSTEAD", False)
if DELETE_INSTEAD:
	delete_samples()
else:
	load()
