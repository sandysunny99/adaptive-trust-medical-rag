try {
    $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/runs/37763028137' -Method Get
    Write-Output ("Status: " + $response.status + " | Conclusion: " + $response.conclusion)
} catch {
    Write-Output "Error: " $_.Exception.Message
}
