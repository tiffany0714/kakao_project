$wd='C:\Users\User\.gemini\antigravity\scratch\kakao_project'
Write-Host "Checking netstat for port 5000..."
$lines = netstat -ano | Select-String ":5000"
if ($lines) {
    foreach ($line in $lines) {
        $parts = ($line -split '\s+') | Where-Object { $_ -ne '' }
        $thepid = $parts[-1]
        Write-Host "Killing PID $thepid"
        try { Stop-Process -Id $thepid -Force -ErrorAction SilentlyContinue } catch { Write-Host "Failed to stop $thepid" }
    }
} else { Write-Host "No netstat entries for :5000" }

Write-Host "Starting server..."
Start-Process -FilePath python -ArgumentList 'run_local_server.py' -WorkingDirectory $wd -WindowStyle Hidden
Start-Sleep -Seconds 2
Write-Host "Running route check script..."
python check_routes_and_set.py
