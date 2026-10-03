# Reproducibility Configuration

*Explicit generation controls are configured where supported to improve reproducibility. Deterministic reproduction is not claimed unless the provider/model supports and honors the required controls.*

## Groq Configuration
A new GenerationConfig object was introduced into the factory initialization to prevent hardcoding. The Groq backend payload was updated to inject these settings:
- Temperature: 0.0
- Max Tokens: None
- Seed: NOT_SUPPORTED (Groq backend default compatibility)

This improves stability while remaining truthful about the limits of provider determinism.
