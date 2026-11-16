fix(live): link only verified evidence sources; stop Cloudflare answers being cut off

Evidence & Sources showed each chunk's corpus URL as plain text. None of the 14 frozen
corpus URLs leads to a verified original: 11 DailyMed links carry placeholder set IDs, one
PubMed ID is attached to two unrelated documents and the openFDA link is the generic API
page. Each evidence item now carries source_link_status and source_link_note, and url is set
only for a link verified for that chunk (verified_source_links, empty until a researcher
approves a source record), so the page never links a possibly wrong document. Unverified
sources stay visible as text with the reason, also in the Markdown export.

The Cloudflare answer model ran without max_tokens, so Workers AI stopped at its 256-token
default and the JSON answer failed to parse. It now gets an explicit 4096-token limit. A
parse failure logs provider, model, finish_reason and length (never the content), marks the
generation stage failed, and says when the model stopped at its token limit.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01REK6hvNTFj2HYEfZiXVJYN
