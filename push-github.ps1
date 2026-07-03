Set-Location -LiteralPath $PSScriptRoot

# Auto-use Windows system proxy (browser uses this, git does not by default)
$proxy = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -ErrorAction SilentlyContinue)
if ($proxy.ProxyEnable -eq 1 -and $proxy.ProxyServer) {
    $proxyUrl = if ($proxy.ProxyServer -match '^https?://') { $proxy.ProxyServer } else { "http://$($proxy.ProxyServer)" }
    git config http.proxy $proxyUrl
    git config https.proxy $proxyUrl
    Write-Host "Using system proxy: $proxyUrl"
} else {
    Write-Host "No system proxy detected"
}

Write-Host ""
Write-Host "Pushing to https://github.com/oo226/egern-config ..."
Write-Host ""

git config --global --unset credential.https://gitee.com.provider 2>$null
git branch -M main 2>$null
git push -u origin main
$code = $LASTEXITCODE

Write-Host ""
if ($code -eq 0) {
    Write-Host "SUCCESS"
    Write-Host "https://github.com/oo226/egern-config"
    Write-Host ""
    Write-Host "Egern URL:"
    Write-Host "https://raw.githubusercontent.com/oo226/egern-config/refs/heads/main/Egern.yaml"
} else {
    Write-Host "FAILED"
    Write-Host "Browser can open GitHub but git needs proxy."
    Write-Host "Current system proxy: $($proxy.ProxyServer)"
}
Write-Host ""
Read-Host "Press Enter to close"
