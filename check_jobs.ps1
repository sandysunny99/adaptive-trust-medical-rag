try {
    $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/runs/37763028137/jobs' -Method Get
    foreach ($job in $response.jobs) {
        Write-Output ("Job: " + $job.name + " | Status: " + $job.status + " | Conclusion: " + $job.conclusion)
    }
} catch {
    Write-Output "Error: " $_.Exception.Message
}
