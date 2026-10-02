# ============================================================
# ShanmugaCLI - Speedtest
# ============================================================

function Start-SpeedTest {

    $width = 58

    function Line($text, $color = "White") {
        $innerWidth = $width - 4

        foreach ($rawLine in ($text -split "`r?`n")) {
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
                Write-Host ("│  " + $line + (" " * $padding) + "  │") -ForegroundColor $color
            }
        }
    }

    function Border($left, $fill, $right) {
        Write-Host ($left + ($fill * ($width - 2)) + $right) -ForegroundColor DarkGray
    }

    Clear-Host

    Border "╭" "─" "╮"

    $title = "SPEED TEST"
    $titlePadding = [math]::Floor(($width - 2 - $title.Length) / 2)

    Write-Host "│" -NoNewline -ForegroundColor DarkGray
    Write-Host (" " * $titlePadding) -NoNewline
    Write-Host $title -NoNewline -ForegroundColor Magenta
    Write-Host (" " * ($width - 2 - $titlePadding - $title.Length)) -NoNewline
    Write-Host "│" -ForegroundColor DarkGray

    Border "├" "─" "┤"

    Line ""
    Line "Connecting to Speedtest..." "Cyan"
    Line ""

    if (-not (Get-Command speedtest.exe -ErrorAction SilentlyContinue)) {
        Line "Speedtest CLI not found." "Red"
        Line ""
        Border "╰" "─" "╯"
        return
    }

    # Run Ookla with a timeout so a stalled network/client cannot freeze the UI.
    $outputFile = [System.IO.Path]::GetTempFileName()
    $errorFile = [System.IO.Path]::GetTempFileName()
    $speedtestProcess = $null

    try {
        $speedtestProcess = Start-Process `
            -FilePath "speedtest.exe" `
            -ArgumentList @("--accept-license", "--accept-gdpr", "-f", "json") `
            -RedirectStandardOutput $outputFile `
            -RedirectStandardError $errorFile `
            -WindowStyle Hidden `
            -PassThru `
            -ErrorAction Stop

        if (-not $speedtestProcess.WaitForExit(30000)) {
            $speedtestProcess.Kill()
            Line "Speedtest timed out after 30 seconds." "Red"
            Line "Check your network connection and try again." "Yellow"
            Line ""
            Border "╰" "─" "╯"
            return
        }

        $raw = Get-Content $outputFile -Raw -ErrorAction SilentlyContinue

        if ([string]::IsNullOrWhiteSpace($raw)) {
            Line "Speedtest failed to return data." "Red"
            Line ""
            Border "╰" "─" "╯"
            return
        }
    }
    catch {
        Line "Could not start Speedtest CLI." "Red"
        Line $_.Exception.Message "Yellow"
        Line ""
        Border "╰" "─" "╯"
        return
    }
    finally {
        Remove-Item $outputFile, $errorFile -Force -ErrorAction SilentlyContinue
    }

    try {
        $result = $raw | ConvertFrom-Json
    }
    catch {
        Line "Could not parse Speedtest results." "Red"
        Line ""
        Border "╰" "─" "╯"
        return
    }

    # --------------------------------------------------------
    # Extract values
    # --------------------------------------------------------

    $ping = [math]::Round($result.ping.latency, 0)

    $downloadMbps = [math]::Round(
        ($result.download.bandwidth * 8) / 1000000,
        2
    )

    $uploadMbps = [math]::Round(
        ($result.upload.bandwidth * 8) / 1000000,
        2
    )

    $server = $result.server.name
    $location = $result.server.location
    $isp = $result.isp
    $resultUrl = $result.result.url

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    Clear-Host

    Border "╭" "─" "╮"

    Write-Host "│" -NoNewline -ForegroundColor DarkGray
    Write-Host (" " * $titlePadding) -NoNewline
    Write-Host $title -NoNewline -ForegroundColor Magenta
    Write-Host (" " * ($width - 2 - $titlePadding - $title.Length)) -NoNewline
    Write-Host "│" -ForegroundColor DarkGray

    Border "├" "─" "┤"

    Line ""

    Line ("◉  PING        {0} ms" -f $ping) "Yellow"
    Line ("↓  DOWNLOAD    {0} Mbps" -f $downloadMbps) "Green"
    Line ("↑  UPLOAD      {0} Mbps" -f $uploadMbps) "Cyan"

    Line ""

    Border "├" "─" "┤"

    Line ("SERVER        {0}" -f $server) "White"
    Line ("LOCATION      {0}" -f $location) "White"
    Line ("ISP           {0}" -f $isp) "White"

    Line ""

    if ($resultUrl) {
        Line "RESULT        Available" "Green"
        Line ""
        Line $resultUrl "Cyan"
    }

    Line ""

    Border "╰" "─" "╯"

    Write-Host ""
}