# ============================================================
# ShanmugaCLI - Speedtest
# ============================================================

function Start-SpeedTest {

    $width = 58

    function Line($text, $color = "White") {
        $padding = $width - 4 - $text.Length
        if ($padding -lt 0) { $padding = 0 }

        Write-Host "│  " -NoNewline -ForegroundColor DarkGray
        Write-Host $text -NoNewline -ForegroundColor $color
        Write-Host (" " * $padding) -NoNewline
        Write-Host "  │" -ForegroundColor DarkGray
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

    # Run Ookla and capture JSON output
    $raw = & speedtest.exe --accept-license --accept-gdpr -f json 2>$null

    if (-not $raw) {
        Line "Speedtest failed to return data." "Red"
        Line ""
        Border "╰" "─" "╯"
        return
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