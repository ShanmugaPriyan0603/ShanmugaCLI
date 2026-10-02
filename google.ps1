# ============================================
#        SHANMUGA CLI - GOOGLE AUTH
# ============================================

$GoogleRoot = "$HOME\ShanmugaCLI\google"
$GoogleCredentials = "$GoogleRoot\credentials.json"
$GoogleToken = "$GoogleRoot\token.json"

function Get-GoogleToken {

    if (-not (Test-Path $GoogleCredentials)) {
        Write-Host ""
        Write-Host "Google credentials.json not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "Expected location:" -ForegroundColor DarkGray
        Write-Host $GoogleCredentials -ForegroundColor Cyan
        Write-Host ""
        return
    }

    python "$HOME\ShanmugaCLI\google_auth.py"
}