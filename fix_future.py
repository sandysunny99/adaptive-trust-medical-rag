import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()
lines = content.split('\n')
# Find the first line that is not a comment or a __future__ import
insert_idx = 0
for i, line in enumerate(lines):
    if line.startswith('from __future__') or line.startswith('\"\"\"') or line.startswith('#'):
        continue
    if line.strip() == '':
        continue
    insert_idx = i
    break

# Extract the injected _lazy_init_models function
lazy_code = []
in_lazy = False
clean_lines = []
for line in lines:
    if line.startswith('def _lazy_init_models(app_state):'):
        in_lazy = True
    if in_lazy:
        lazy_code.append(line)
        if line.strip() == 'app_state.retrieval_engine = None':
            in_lazy = False
    else:
        clean_lines.append(line)

# Put lazy_code at insert_idx
final_lines = clean_lines[:insert_idx] + lazy_code + ['\n'] + clean_lines[insert_idx:]
open(file_path, 'w').write('\n'.join(final_lines))
