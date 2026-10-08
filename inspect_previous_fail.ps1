try {
    $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/runs/37295253483/jobs' -Method Get
    foreach ($job in $response.jobs) {
        Write-Output ("Job: " + $job.name + " | Status: " + $job.status + " | Conclusion: " + $job.conclusion)
        if ($job.conclusion -eq "failure") {
            Write-Output ("Fetching logs for failed job: " + $job.id)
            $logUrl = "https://api.github.com/repos/sandysunny99/adaptive-trust-medical-rag/actions/jobs/" + $job.id + "/logs"
            try {
                $logContent = Invoke-RestMethod -Uri $logUrl -Method Get
                $lines = $logContent -split "
"
                $lastLines = $lines[-30..-1]
                Write-Output "--- LAST 30 LINES OF FAILED JOB LOG ---"
                foreach ($line in $lastLines) {
                    Write-Output $line
                }
                Write-Output "----------------------------------------"
            } catch {
                Write-Output "Could not fetch log directly due to redirect or format."
            }
        }
    }
} catch {
    Write-Output "Error: " $_.Exception.Message
}
