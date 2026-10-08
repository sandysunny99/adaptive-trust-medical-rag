try {
    $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/runs?branch=main' -Method Get
    $runs = $response.workflow_runs | Select-Object -First 5
    foreach ($run in $runs) {
        Write-Output ("Run: " + $run.id + " | Status: " + $run.status + " | Conclusion: " + $run.conclusion + " | Commit: " + $run.head_sha + " | Workflow: " + $run.name)
    }
} catch {
    Write-Output "Error: " $_.Exception.Message
}
