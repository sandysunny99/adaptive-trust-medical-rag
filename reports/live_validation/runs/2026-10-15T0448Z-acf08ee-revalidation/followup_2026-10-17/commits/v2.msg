feat(live): load approved V2 relationship records with their own versioned evidence

A V1 record must cite a chunk of the frozen live corpus, so exact label text captured from
DailyMed could not support a record without changing the frozen corpus. LIVE_RELATIONSHIP_RECORDS_V2
has its own records file, evidence file and manifest. Nothing loads unless the manifest is
APPROVED by a named person on a recorded date and both file hashes match. An evidence chunk
must be complete, keep its content hash, carry an https URL and an embedding of the corpus
dimension, and never reuse a frozen chunk id; it joins retrieval only when an accepted V2
record cites it, and then passes the existing hash, trust, eligibility and claim-verification
gates. V1 records still cite only the frozen corpus. No V2 dataset is shipped, so the live
application is unchanged until a researcher approves one.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
