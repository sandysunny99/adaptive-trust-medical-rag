try {
    Invoke-WebRequest -Uri 'https://github.com/sandysunny99/adaptive-trust-medical-rag/archive/refs/heads/main.zip' -OutFile 'repo.zip'
    # Actually, the logs url is https://github.com/sandysunny99/adaptive-trust-medical-rag/actions/runs/37295253483/logs
} catch {}
