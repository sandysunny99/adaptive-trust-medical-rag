import glob
files = [
    'RECENT_COMMIT_FORENSIC_REVIEW.md',
    'TEST_BYPASS_AND_SKIP_AUDIT.md',
    'PLACEHOLDER_TEST_AUDIT.md',
    'RUFF_REMEDIATION_AUDIT.md',
    'BANDIT_REMEDIATION_AUDIT.md',
    'GITHUB_FINAL_CHECK_STATUS.md',
    'LIVE_APP_FINAL_HEALTH_REPORT.md',
    'V1_3_PREAUTHORIZATION_REVALIDATION_V3.md'
]
content = "# Consolidated Forensic Audit Log\n\n"
for f in files:
    try:
        with open(f, 'r') as fp:
            content += f"---\n\n## Source: {f}\n\n{fp.read()}\n\n"
    except Exception as e:
        pass
with open('temp_forensic.txt', 'w') as out:
    out.write(content)
