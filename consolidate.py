import glob
files = glob.glob('*_V2.md') + glob.glob('*_V3.md') + glob.glob('*_AUDIT.md') + ['RECENT_COMMIT_FORENSIC_REVIEW.md', 'FREE_LLM_PROVIDER_SELECTION_ANALYSIS.md', 'GITHUB_FINAL_CHECK_STATUS.md', 'LIVE_APP_FINAL_HEALTH_REPORT.md']

content = []
for f in files:
    with open(f, 'r') as fp:
        content.append(f'---\n\n## Source: {f}\n')
        content.append(fp.read())

open('CONSOLIDATED_FORENSIC_REPORT.md', 'w').write('\n'.join(content))
