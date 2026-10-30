# ============================================
#       SHANMUGA CLI - NOTES
# ============================================

function Get-NoteInput {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$InputText
    )

    if ($InputText.Count -gt 0) {
        return ($InputText -join " ")
    }

    $pipedInput = @($input | ForEach-Object { $_.ToString() })
    if ($pipedInput.Count -gt 0) {
        return ($pipedInput -join [Environment]::NewLine)
    }

    return Read-Host "Note"
}

function Invoke-QNote {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$InputText
    )

    $noteText = Get-NoteInput @InputText
    $downloadsPath = Join-Path $HOME "Downloads"

    if (-not (Test-Path -LiteralPath $downloadsPath -PathType Container)) {
        New-Item -ItemType Directory -Path $downloadsPath -Force | Out-Null
    }

    $fileName = "note-{0}.txt" -f (Get-Date -Format "yyyyMMdd-HHmmss")
    $filePath = Join-Path $downloadsPath $fileName
    Set-Content -LiteralPath $filePath -Value $noteText -Encoding utf8

    Write-Host "Note saved to $filePath" -ForegroundColor Green
}

function Invoke-Note {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$InputText
    )

    $noteText = Get-NoteInput @InputText
    $fileName = Read-Host "File name"
    $saveLocation = Read-Host "Save location"

    if ([string]::IsNullOrWhiteSpace($fileName)) {
        Write-Host "File name cannot be empty." -ForegroundColor Red
        return
    }

    if ([string]::IsNullOrWhiteSpace($saveLocation)) {
        Write-Host "Save location cannot be empty." -ForegroundColor Red
        return
    }

    if (-not [IO.Path]::HasExtension($fileName)) {
        $fileName = "$fileName.txt"
    }

    if (-not (Test-Path -LiteralPath $saveLocation -PathType Container)) {
        New-Item -ItemType Directory -Path $saveLocation -Force | Out-Null
    }

    $filePath = Join-Path $saveLocation $fileName
    Set-Content -LiteralPath $filePath -Value $noteText -Encoding utf8

    Write-Host "Note saved to $filePath" -ForegroundColor Green
}

Set-Alias qnote Invoke-QNote
Set-Alias note Invoke-Note
