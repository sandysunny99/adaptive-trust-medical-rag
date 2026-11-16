feat(live): name the provider and model that served every outcome

Abstentions and output errors did not say which model produced the text they judged, so a
run could not be traced to its provider. Each event after generation now carries served_by,
read from the provider's response (provider, model, the provider-reported model, stop reason
and output length), never the user's selection or the output itself. An abstention before
generation and a provider failure say no model served them. The image extraction event and
its error name the vision provider and model, and each RxNorm entity says how the normalizer
resolved it (rxnorm_source), which an image's VISION source label otherwise hides.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01REK6hvNTFj2HYEfZiXVJYN
