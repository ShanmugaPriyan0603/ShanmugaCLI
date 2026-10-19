# ============================================
#          SHANMUGA CLI - COMPRESS
# ============================================

$CompressPython = Join-Path $PSScriptRoot "compress.py"

function Show-CompressBox {
    param(
        [string]$Title,
        [string]$Message,
        [ConsoleColor]$Color = "Magenta"
    )

    $width = 58
    $innerWidth = $width - 4

    Write-Host ""
    Write-Host ("╭" + ("─" * ($width - 2)) + "╮") -ForegroundColor $Color

    if ($Title.Length -gt $innerWidth) {
        $Title = $Title.Substring(0, $innerWidth - 3) + "..."
    }

    $titlePadding = $innerWidth - $Title.Length
    $titleLeft = [math]::Floor($titlePadding / 2)
    $titleRight = $titlePadding - $titleLeft
    Write-Host ("│ " + (" " * $titleLeft) + $Title + (" " * $titleRight) + " │") -ForegroundColor $Color
    Write-Host ("├" + ("─" * ($width - 2)) + "┤") -ForegroundColor $Color

    foreach ($rawLine in ($Message -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($rawLine)) {
            $wrappedLines = @("")
        }
        else {
            $wrappedLines = @()
            $line = ""

            foreach ($word in ($rawLine.Trim() -split "\s+")) {
                if ($word.Length -gt $innerWidth) {
                    if ($line.Length -gt 0) {
                        $wrappedLines += $line
                        $line = ""
                    }

                    while ($word.Length -gt $innerWidth) {
                        $wrappedLines += $word.Substring(0, $innerWidth)
                        $word = $word.Substring($innerWidth)
                    }
                }

                if ($line.Length -eq 0) {
                    $line = $word
                }
                elseif (($line.Length + 1 + $word.Length) -le $innerWidth) {
                    $line += " $word"
                }
                else {
                    $wrappedLines += $line
                    $line = $word
                }
            }

            if ($line.Length -gt 0) {
                $wrappedLines += $line
            }
        }

        foreach ($line in $wrappedLines) {
            Write-Host ("│ " + $line + (" " * ($innerWidth - $line.Length)) + " │") -ForegroundColor White
        }
    }

    Write-Host ("╰" + ("─" * ($width - 2)) + "╯") -ForegroundColor $Color
    Write-Host ""
}

function Invoke-CompressPython {
    param(
        [string[]]$Arguments
    )

    $raw = & python $CompressPython @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        $message = ($raw | Select-Object -Last 1).ToString()
        try {
            $errorResult = $raw | ConvertFrom-Json
            $message = $errorResult.error
        }
        catch {
            if ([string]::IsNullOrWhiteSpace($message)) {
                $message = "The compression backend failed."
            }
        }

        Show-CompressBox -Title "COMPRESSION FAILED" -Message $message -Color Red
        return $null
    }

    try {
        return $raw | ConvertFrom-Json
    }
    catch {
        Show-CompressBox -Title "COMPRESSION FAILED" -Message "The compression backend returned an invalid response." -Color Red
        return $null
    }
}

function Invoke-Compress {
    if (-not (Test-Path -LiteralPath $CompressPython -PathType Leaf)) {
        Show-CompressBox -Title "COMPRESS" -Message "Compression backend not found:`n$CompressPython" -Color Red
        return
    }

    Show-CompressBox -Title "FILE COMPRESSOR" -Message "Enter the path of the JPG, PNG, or PDF file to compress:"
    $inputPath = (Read-Host "  >").Trim().Trim('"')

    if ([string]::IsNullOrWhiteSpace($inputPath)) {
        Show-CompressBox -Title "NO FILE SELECTED" -Message "A file path is required." -Color Yellow
        return
    }

    try {
        $file = Get-Item -LiteralPath $inputPath -ErrorAction Stop
    }
    catch {
        Show-CompressBox -Title "FILE NOT FOUND" -Message "Could not find:`n$inputPath" -Color Red
        return
    }

    if (-not $file.PSIsContainer) {
        $extension = $file.Extension.ToLowerInvariant()
        if ($extension -notin @(".jpg", ".jpeg", ".png", ".pdf")) {
            Show-CompressBox -Title "UNSUPPORTED FILE" -Message "Supported files are JPG, PNG, and PDF." -Color Yellow
            return
        }
    }
    else {
        Show-CompressBox -Title "UNSUPPORTED PATH" -Message "Please select a file, not a folder." -Color Yellow
        return
    }

    Show-CompressBox -Title "FILE SELECTED" -Message "Name: $($file.Name)`nType: $($file.Extension.ToUpperInvariant())`n`n1. Compress size`n2. Compress to ZIP"
    $method = Read-Host "Choose an option (1-2)"

    if ($method -eq "2") {
        $output = Invoke-CompressPython -Arguments @("zip", "--path", $file.FullName)
    }
    elseif ($method -eq "1") {
        if ($extension -eq ".pdf") {
            $qualityMessage = "1. High - lossless structural cleanup, usually the largest file`n2. Balanced - stronger PDF stream compression, quality stays unchanged`n3. Small - strongest structural cleanup, quality stays unchanged"
        }
        else {
            $qualityMessage = "1. High quality - smallest quality change, larger file`n2. Balanced - good size reduction with minor quality loss`n3. Small file - strongest reduction, visible quality loss"
        }

        Show-CompressBox -Title "COMPRESSION QUALITY" -Message $qualityMessage
        $levelChoice = Read-Host "Choose a range (1-3)"
        $levels = @{ "1" = "high"; "2" = "balanced"; "3" = "small" }

        if (-not $levels.ContainsKey($levelChoice)) {
            Show-CompressBox -Title "INVALID OPTION" -Message "Choose 1, 2, or 3." -Color Yellow
            return
        }

        $output = Invoke-CompressPython -Arguments @("compress", "--path", $file.FullName, "--level", $levels[$levelChoice])
    }
    else {
        Show-CompressBox -Title "INVALID OPTION" -Message "Choose 1 or 2." -Color Yellow
        return
    }

    if ($null -eq $output -or -not $output.ok) {
        return
    }

    $savedSize = "{0:N1} KB" -f ($output.compressed_size / 1KB)
    $originalSize = "{0:N1} KB" -f ($output.original_size / 1KB)
    Show-CompressBox -Title "COMPRESSION COMPLETE" -Message "File: $($file.Name)`nOriginal: $originalSize`nCompressed: $savedSize`n`nSave the compressed file here?`n$($output.destination)" -Color Green
    $save = Read-Host "Save file? (y/n)"

    if ($save -notmatch "^(y|yes)$") {
        Remove-Item -LiteralPath $output.destination -Force -ErrorAction SilentlyContinue
        Show-CompressBox -Title "NOT SAVED" -Message "The compressed file was deleted." -Color Yellow
        return
    }

    $deleteOriginal = Read-Host "Delete the original file? (y/n)"
    if ($deleteOriginal -match "^(y|yes)$") {
        try {
            Remove-Item -LiteralPath $file.FullName -Force -ErrorAction Stop
            Show-CompressBox -Title "FILE SAVED" -Message "Saved in the same directory as the original:`n$($output.destination)`n`nOriginal file deleted." -Color Green
        }
        catch {
            Show-CompressBox -Title "FILE SAVED" -Message "Saved in the same directory as the original:`n$($output.destination)`n`nCould not delete the original file:`n$($_.Exception.Message)" -Color Yellow
        }
    }
    else {
        Show-CompressBox -Title "FILE SAVED" -Message "Saved in the same directory as the original:`n$($output.destination)`n`nOriginal file kept." -Color Green
    }
}

Set-Alias compress Invoke-Compress
