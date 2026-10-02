function Show-QRBox {

    param(
        [string]$Title,
        [string]$Message
    )

    $width = 58
    $innerWidth = $width - 4

    Write-Host ""
    Write-Host ("╭" + ("─" * ($width - 2)) + "╮") -ForegroundColor Magenta

    if ($Title.Length -gt $innerWidth) {
        $Title = $Title.Substring(0, $innerWidth - 3) + "..."
    }

    $titlePadding = $innerWidth - $Title.Length
    $titleLeft = [math]::Floor($titlePadding / 2)
    $titleRight = $titlePadding - $titleLeft

    Write-Host ("│ " + (" " * $titleLeft) + $Title + (" " * $titleRight) + " │") -ForegroundColor Magenta
    Write-Host ("├" + ("─" * ($width - 2)) + "┤") -ForegroundColor Magenta

    foreach ($rawLine in ($Message -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($rawLine)) {
            $wrappedLines = @("")
        }
        else {
            $wrappedLines = @()
            $remaining = $rawLine.Trim()

            while ($remaining.Length -gt $innerWidth) {
                $breakAt = $remaining.LastIndexOf(" ", $innerWidth)

                if ($breakAt -le 0) {
                    $breakAt = $innerWidth
                }

                $wrappedLines += $remaining.Substring(0, $breakAt).TrimEnd()
                $remaining = $remaining.Substring($breakAt).TrimStart()
            }

            $wrappedLines += $remaining
        }

        foreach ($line in $wrappedLines) {
            $padding = $innerWidth - $line.Length
            Write-Host ("│ " + $line + (" " * $padding) + " │") -ForegroundColor White
        }
    }

    Write-Host ("╰" + ("─" * ($width - 2)) + "╯") -ForegroundColor Magenta
    Write-Host ""
}

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
        Show-QRBox -Title "QR CODE GENERATOR" -Message "Enter text or URL:"

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