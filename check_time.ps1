try {
    $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/runs/37763028137' -Method Get
    Write-Output ("Started At: " + $response.created_at)
} catch {
    Write-Output "Error: " $_.Exception.Message
}
