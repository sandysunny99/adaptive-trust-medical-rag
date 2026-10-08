import sys

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
lines = open(file_path).read().split('\n')

lazy_code = []
clean_lines = []
in_lazy = False

for line in lines:
    if line.startswith('def _lazy_init_models(app_state):'):
        in_lazy = True
    if in_lazy:
        lazy_code.append(line)
        if line.strip() == 'app_state.retrieval_engine = None':
            in_lazy = False
    else:
        clean_lines.append(line)

# find the last import statement to insert after
insert_idx = 0
for i, line in enumerate(clean_lines):
    if line.startswith('import ') or line.startswith('from '):
        insert_idx = i + 1

final_lines = clean_lines[:insert_idx] + ['\n'] + lazy_code + ['\n'] + clean_lines[insert_idx:]
open(file_path, 'w').write('\n'.join(final_lines))
