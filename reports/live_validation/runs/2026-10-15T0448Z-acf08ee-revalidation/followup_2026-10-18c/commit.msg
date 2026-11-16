test(vision): reject invalid content inside a code fence

The vision parser unwraps a code fence only around one valid JSON object. Lock in that
malformed JSON, prose, nested fences, schema-invalid JSON inside a fence and an unclosed
fence all fail closed with SCHEMA_ERROR. Test-only; the committed parser already rejects
every case.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
