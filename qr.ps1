function Invoke-QR {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$InputText
    )

    Import-Module PSQR -ErrorAction Stop

    # If text was supplied: qr "https://example.com"
    if ($InputText.Count -gt 0) {
        $text = $InputText -join " "
    }
    else {
        Write-Host ""
        Write-Host "╭─ QR CODE GENERATOR ─────────────────────────────────────╮" -ForegroundColor Magenta
        Write-Host "│                                                        │" -ForegroundColor Magenta
        Write-Host "│  Enter text or URL:                                    │" -ForegroundColor Magenta
        Write-Host "╰────────────────────────────────────────────────────────╯" -ForegroundColor Magenta
        Write-Host ""

        $text = Read-Host "  >"

        if ([string]::IsNullOrWhiteSpace($text)) {
            Write-Host ""
            Write-Host "  ✕ Nothing entered." -ForegroundColor Red
            Write-Host ""
            return
        }
    }

    Write-Host ""
    Write-Host "  QR Code" -ForegroundColor Cyan
    Write-Host "  ──────────────────────────────────────────────────────" -ForegroundColor DarkGray
    Write-Host ""

    New-PSQR -Text $text

    Write-Host ""
}
Set-Alias qr Invoke-QR