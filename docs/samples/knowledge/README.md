# Sample knowledge documents

**Every file here is invented.** They exist so the document-knowledge
pipeline can be exercised end to end without waiting for real UCC policies,
and so the retrieval tests have something with real structure (headings,
sections, numbers) to search.

Each file says SAMPLE in its first line, so a chunk retrieved from one is
self-identifying even out of context.

Load them:

```
bench --site <site> console
>>> exec(open("apps/ucc_intelligence/../docs/migration/scripts/load_sample_knowledge.py").read(), globals())
```

Remove them again:

```
>>> DELETE_INSTEAD = True
>>> exec(open(".../load_sample_knowledge.py").read(), globals())
```

Real documents replace these; they are not a starting corpus to build on.
