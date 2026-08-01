# Recorded, not designed

Things Felix has asked for that are not being built yet. Recorded here so they
are not lost, and so nothing built in the meantime quietly makes them harder.

Not a design document. Nothing below has been decided.

---

## Point-in-time snapshots of a criterion tab

**Asked for:** 2026-08-02.

> "I want point-in-time snapshots eventually -- the ability to view a criterion
> tab as it stood on a given date, so audit evidence doesn't shift underneath
> me. Don't design it yet, just don't build anything that would make it harder
> later."

### What the requirement is really about

An EduTrust auditor is shown a criterion tab. Six months later somebody asks
what that tab said on the day. Today the answer is "whatever the live query
returns now", which is not evidence -- it is a live report that happens to have
been printed once.

Two distinct things can shift underneath a tab, and they need separating
before anything is designed:

1. **The configuration** -- which charts are on the tab, at what size, in what
   order, with what intro text and which questions visible.
2. **The figures** -- what the queries returned on that date.

(1) is Sophia's own data. (2) is the institution's operational data, which
lives in ERPNext and legitimately changes.

### What already helps, and must not be undone

- **`UCC Analytics Tab Change`** records every configuration change with the
  before AND after value, the user and the timestamp. That is already a
  complete, append-only history of (1). Reconstructing a tab's configuration
  on a given date is replaying those records -- no new capture is needed. This
  is the single most important thing not to weaken: the DocType grants
  create/write to nobody and its controller refuses edits, so the history
  cannot be rewritten after the fact.
- **Institution-wide storage** (`UCC Analytics Tab`, one record per
  criterion+tab) means there is one configuration to snapshot, not one per
  user. Per-user storage would have made "the tab as it stood" ambiguous.
- **`Export PDF`** already produces a stamped, dated artefact of both (1) and
  (2) together. It is a manual snapshot, and for now it is the honest answer
  to "capture what the auditor saw".

### What would make it harder, and is therefore avoided

- Deleting or compacting `UCC Analytics Tab Change` records. A retention
  policy that prunes them would destroy the only record of (1).
- Storing configuration anywhere without an audit write.
- Recording a change as "the intro was edited" without the before/after text.
  A summary alone cannot reconstruct a state.
- Making the audit DocType writable for any reason.

### The open question, for when it is designed

Whether (2) needs capturing at all, or whether a snapshot means "the tab's
configuration as it stood, re-run against today's data, with the difference
made visible". Capturing figures means storing query results -- institutional
data, with retention, permission and PDPA consequences that configuration
history does not have. That is the decision to take first, and it is not taken
here.
