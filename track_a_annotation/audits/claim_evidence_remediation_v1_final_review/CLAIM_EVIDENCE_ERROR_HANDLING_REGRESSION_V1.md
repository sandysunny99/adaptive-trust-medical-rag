# ERROR HANDLING REGRESSION
- Missing citation -> `UNSUPPORTED`
- Invalid citation -> `UNSUPPORTED`
- `NLIInferenceError` -> `neutral=1.0` -> `INSUFFICIENT_EVIDENCE` (fail-closed)
- Missing trust/relationship -> Defaults to `[]` and `None`. Claim may pass if text entails, but will lack metadata for explicit block policies.
