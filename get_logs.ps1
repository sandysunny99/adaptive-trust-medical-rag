try {
    $log = Invoke-RestMethod -Uri 'https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/jobs/111714834173/logs' -Method Get
    $lines = $log -split "
"
    $lines[-100..-1] | ForEach-Object { Write-Output $_ }
} catch {
    Write-Output "Error: " $_.Exception.Message
}
