# ============================================
#          SHANMUGA CLI - FOCUS MODE
# ============================================

$FocusRoot = "$HOME\ShanmugaCLI\focus"
$FocusStateFile = "$FocusRoot\active.json"
$FocusHistoryFile = "$FocusRoot\history.json"
$FocusConfigFile = "$FocusRoot\config.json"

# --------------------------------------------
# Ensure directories exist
# --------------------------------------------

if (-not (Test-Path $FocusRoot)) {
    New-Item -ItemType Directory -Path $FocusRoot -Force | Out-Null
}


# ============================================
#              DEFAULT CONFIG
# ============================================

if (-not (Test-Path $FocusConfigFile)) {

    $defaultConfig = @{
        blocked_apps = @(
            "Discord.exe",
            "Steam.exe",
	    "D:\Movies and TV\Genshin Impact\HoYoPlay\games\Genshin Impact game\GenshinImpact.exe"
        )
    }

    $defaultConfig |
        ConvertTo-Json -Depth 5 |
        Set-Content $FocusConfigFile
}


# ============================================
#             FOCUS UI HELPERS
# ============================================

function Show-FocusBox {

    param(
        [string]$Title,
        [string]$Message,
        [ConsoleColor]$Color = "Cyan",
        [int]$MaxWidth = 76
    )

    $consoleWidth = $MaxWidth

    try {
        if ([Console]::WindowWidth -gt 0) {
            $consoleWidth = [math]::Min($MaxWidth, [Console]::WindowWidth - 2)
        }
    }
    catch {
        $consoleWidth = $MaxWidth
    }

    $width = [math]::Max(40, $consoleWidth)
    $innerWidth = $width - 4
    $lines = @()

    foreach ($rawLine in ($Message -split "`r?`n")) {
        if ([string]::IsNullOrWhiteSpace($rawLine)) {
            $lines += ""
            continue
        }

        $remaining = $rawLine.Trim()

        while ($remaining.Length -gt $innerWidth) {
            $breakAt = $remaining.LastIndexOf(" ", $innerWidth)

            if ($breakAt -le 0) {
                $breakAt = $innerWidth
            }

            $lines += $remaining.Substring(0, $breakAt).TrimEnd()
            $remaining = $remaining.Substring($breakAt).TrimStart()
        }

        $lines += $remaining
    }

    if ($Title.Length -gt $innerWidth) {
        $titleText = $Title.Substring(0, $innerWidth - 3) + "..."
    }
    else {
        $titleText = $Title
    }

    $titlePadding = $innerWidth - $titleText.Length
    $titleLeft = [math]::Floor($titlePadding / 2)
    $titleRight = $titlePadding - $titleLeft

    Write-Host ""
    Write-Host ("╭" + ("─" * ($width - 2)) + "╮") -ForegroundColor DarkCyan
    Write-Host ("│ " + (" " * $titleLeft) + $titleText + (" " * $titleRight) + " │") -ForegroundColor $Color
    Write-Host ("├" + ("─" * ($width - 2)) + "┤") -ForegroundColor DarkCyan

    foreach ($line in $lines) {
        $padding = $innerWidth - $line.Length
        Write-Host ("│ " + $line + (" " * $padding) + " │") -ForegroundColor White
    }

    Write-Host ("╰" + ("─" * ($width - 2)) + "╯") -ForegroundColor DarkCyan
    Write-Host ""
}

# ============================================
#             LOAD FOCUS HISTORY
# ============================================

function Get-FocusHistory {

    if (-not (Test-Path $FocusHistoryFile)) {
        return @()
    }

    try {
        $data = Get-Content $FocusHistoryFile -Raw |
            ConvertFrom-Json

        if ($null -eq $data) {
            return @()
        }

        return @($data)
    }
    catch {
        return @()
    }
}


# ============================================
#             SAVE FOCUS HISTORY
# ============================================

function Save-FocusHistory {

    param(
        [array]$History
    )

    $History |
        ConvertTo-Json -Depth 10 |
        Set-Content $FocusHistoryFile
}


# ============================================
#              ACTIVE SESSION
# ============================================

function Get-ActiveFocus {

    if (-not (Test-Path $FocusStateFile)) {
        return $null
    }

    try {
        return Get-Content $FocusStateFile -Raw |
            ConvertFrom-Json
    }
    catch {
        return $null
    }
}


function Save-ActiveFocus {

    param(
        $Session
    )

    $Session |
        ConvertTo-Json -Depth 10 |
        Set-Content $FocusStateFile
}


function Clear-ActiveFocus {

    if (Test-Path $FocusStateFile) {
        Remove-Item $FocusStateFile -Force
    }
}


# ============================================
#              WINDOWS NOTIFICATION
# ============================================

function Show-FocusNotification {

    param(
        [string]$Title,
        [string]$Message
    )

    try {

        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing

        $notify = New-Object System.Windows.Forms.NotifyIcon

        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = $Title
        $notify.BalloonTipText = $Message
        $notify.Visible = $true

        $notify.ShowBalloonTip(10000)

        Start-Sleep -Seconds 10

        $notify.Dispose()
    }
    catch {

        # Fallback: make the terminal itself noticeable
        [console]::beep(1000, 500)
        [console]::beep(1200, 500)
        [console]::beep(1000, 500)
    }
}


# ============================================
#             DURATION SELECTOR
# ============================================

function Select-FocusDuration {

    $options = @(
        "15 minutes",
        "25 minutes",
        "30 minutes",
        "45 minutes",
        "60 minutes",
        "90 minutes",
        "120 minutes",
        "Custom"
    )

    $index = 2

    while ($true) {

        Clear-Host

        Write-Host ""
        Write-Host ("╭" + ("─" * 54) + "╮") -ForegroundColor DarkCyan
        Write-Host ("│" + (" " * 20) + "FOCUS DURATION" + (" " * 20) + "│") -ForegroundColor Cyan
        Write-Host ("├" + ("─" * 54) + "┤") -ForegroundColor DarkCyan
        Write-Host ""

        for ($i = 0; $i -lt $options.Count; $i++) {

            if ($i -eq $index) {
                Write-Host "    > $($options[$i])" -ForegroundColor Cyan
            }
            else {
                Write-Host "      $($options[$i])" -ForegroundColor DarkGray
            }
        }

        Write-Host ""
        Write-Host "    ↑ / ↓   Select" -ForegroundColor DarkGray
        Write-Host "    Enter   Confirm" -ForegroundColor DarkGray
        Write-Host ""

        $key = [Console]::ReadKey($true)

        switch ($key.Key) {

            "UpArrow" {
                $index--

                if ($index -lt 0) {
                    $index = $options.Count - 1
                }
            }

            "DownArrow" {
                $index++

                if ($index -ge $options.Count) {
                    $index = 0
                }
            }

            "Enter" {

                if ($index -eq ($options.Count - 1)) {

                    $custom = Read-Host "Enter duration in minutes"

                    $minutes = 0

                    if ([int]::TryParse($custom, [ref]$minutes)) {

                        if ($minutes -gt 0) {
                            return $minutes
                        }
                    }

                    Write-Host ""
                    Write-Host "Invalid duration." -ForegroundColor Red
                    Start-Sleep -Seconds 1

                }
                else {

                    switch ($index) {
                        0 { return 15 }
                        1 { return 25 }
                        2 { return 30 }
                        3 { return 45 }
                        4 { return 60 }
                        5 { return 90 }
                        6 { return 120 }
                    }
                }
            }
        }
    }
}


# ============================================
#             BLOCKED APPLICATIONS
# ============================================

function Get-BlockedApplications {

    try {

        $config = Get-Content $FocusConfigFile -Raw |
            ConvertFrom-Json

        return @($config.blocked_apps)
    }
    catch {

        return @()
    }
}


function Stop-BlockedApplications {

    $apps = Get-BlockedApplications

    foreach ($app in $apps) {

        $processName = [System.IO.Path]::GetFileNameWithoutExtension($app)

        Get-Process -Name $processName -ErrorAction SilentlyContinue |
            Stop-Process -Force -ErrorAction SilentlyContinue
    }
}


# ============================================
#             BLOCKER MONITOR
# ============================================

function Start-FocusBlocker {

    $script = @"
while (Test-Path '$FocusStateFile') {

    try {

        \$state = Get-Content '$FocusStateFile' -Raw |
            ConvertFrom-Json

        if ((Get-Date) -ge ([datetime]::Parse(\$state.end_time))) {
            break
        }

        \$apps = Get-Content '$FocusConfigFile' -Raw |
            ConvertFrom-Json

        foreach (\$app in @(\$apps.blocked_apps)) {

            \$name = [System.IO.Path]::GetFileNameWithoutExtension(\$app)

            Get-Process -Name \$name -ErrorAction SilentlyContinue |
                Stop-Process -Force -ErrorAction SilentlyContinue
        }

    } catch {}

    Start-Sleep -Seconds 2
}
"@

    $encoded = [Convert]::ToBase64String(
        [Text.Encoding]::Unicode.GetBytes($script)
    )

    Start-Process powershell.exe `
        -ArgumentList "-NoProfile -EncodedCommand $encoded" `
        -WindowStyle Hidden
}


# ============================================
#             FOCUS STATUS
# ============================================

function focusstatus {

    $session = Get-ActiveFocus

    if ($null -eq $session) {

        Show-FocusBox `
            "NO ACTIVE FOCUS" `
            "There is currently no active focus session." `
            "Yellow"

        return
    }

    $end = [datetime]::Parse($session.end_time)
    $remaining = $end - (Get-Date)

    if ($remaining.TotalSeconds -le 0) {

        Show-FocusBox `
            "FOCUS FINISHED" `
            "$($session.title)`n`nThe session has reached its end time." `
            "Green"

        return
    }

    $hours = [math]::Floor($remaining.TotalHours)
    $minutes = $remaining.Minutes
    $seconds = $remaining.Seconds

    if ($hours -gt 0) {
        $time = "{0:D2}:{1:D2}:{2:D2}" -f $hours, $minutes, $seconds
    }
    else {
        $time = "{0:D2}:{1:D2}" -f $minutes, $seconds
    }

    Show-FocusBox `
        "FOCUS ACTIVE" `
        "$($session.title)`n`nTime remaining: $time`n`nStarted: $([datetime]::Parse($session.start_time).ToString('hh:mm tt'))`nEnds:    $end.ToString('hh:mm tt')" `
        "Cyan"
}


# ============================================
#             STOP FOCUS SESSION
# ============================================

function focusstop {

    $session = Get-ActiveFocus

    if ($null -eq $session) {

        Write-Host ""
        Write-Host "No active focus session." -ForegroundColor DarkGray
        Write-Host ""

        return
    }

    Write-Host ""
    Write-Host "Stop focus session '$($session.title)'? (y/n)" -ForegroundColor Yellow

    $answer = Read-Host

    if ($answer -notmatch "^(y|yes)$") {
        return
    }

    $history = @(Get-FocusHistory)

    $session | Add-Member -NotePropertyName "completed" -NotePropertyValue $false -Force
    $session | Add-Member -NotePropertyName "ended_at" -NotePropertyValue (Get-Date).ToString("o") -Force
    $session | Add-Member -NotePropertyName "reflection" -NotePropertyValue "Session stopped manually." -Force

    $history += $session

    Save-FocusHistory $history
    Clear-ActiveFocus

    Show-FocusBox `
        "FOCUS STOPPED" `
        "$($session.title)`n`nSession marked as interrupted." `
        "Yellow"
}


# ============================================
#                DELETE HISTORY
# ============================================

function focusdelete {

    $history = @(Get-FocusHistory)

    if ($history.Count -eq 0) {
        Show-FocusBox `
            "NO HISTORY" `
            "There are no focus sessions to delete." `
            "Yellow"

        return
    }

    $answer = Read-Host "Delete all focus history? (y/n)"

    if ($answer -notmatch "^(y|yes)$") {
        Write-Host "History deletion cancelled." -ForegroundColor DarkGray
        return
    }

    if (Test-Path $FocusHistoryFile) {
        Remove-Item $FocusHistoryFile -Force
    }

    Show-FocusBox `
        "HISTORY DELETED" `
        "All saved focus sessions have been deleted." `
        "Green"
}


# ============================================
#                 FOCUS HELP
# ============================================

function focushelp {

    Show-FocusBox `
        "FOCUS COMMANDS" `
        "focus                  Start a focus session`n`nfocus status           Show the active session and remaining time`nfocus stop             Stop the active session`nfocus delete           Delete all saved focus history`nfocus history          View recent focus sessions`nfocus stats            View focus statistics`nfocus config           Show blocked applications`nfocus help             Show this command list" `
        "Cyan"
}


# ============================================
#                 START FOCUS
# ============================================

function focus {

    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    # ----------------------------------------
    # Subcommands
    # ----------------------------------------

    if ($Args.Count -gt 0) {

        switch ($Args[0].ToLower()) {

            "help" {
                focushelp
                return
            }

            "commands" {
                focushelp
                return
            }

            "?" {
                focushelp
                return
            }

            "-h" {
                focushelp
                return
            }

            "status" {
                focusstatus
                return
            }

            "stop" {
                focusstop
                return
            }

            "delete" {
                focusdelete
                return
            }

            "history" {
                focushistory
                return
            }

            "stats" {
                focusstats
                return
            }

            "config" {
                focusconfig
                return
            }
        }
    }


    # ----------------------------------------
    # Prevent multiple sessions
    # ----------------------------------------

    $existing = Get-ActiveFocus

    if ($null -ne $existing) {

        Show-FocusBox `
            "FOCUS ALREADY ACTIVE" `
            "$($existing.title)`n`nUse 'focus status' to see the timer.`nUse 'focus stop' to end it." `
            "Yellow"

        return
    }


    # ----------------------------------------
    # Select duration
    # ----------------------------------------

    $minutes = Select-FocusDuration


    # ----------------------------------------
    # Title
    # ----------------------------------------

    Clear-Host

    Write-Host ""
    Write-Host "FOCUS SESSION" -ForegroundColor Cyan
    Write-Host "──────────────" -ForegroundColor DarkCyan
    Write-Host ""

    $title = Read-Host "What are you focusing on?"

    if ([string]::IsNullOrWhiteSpace($title)) {
        $title = "Focus Session"
    }


    # ----------------------------------------
    # Create session
    # ----------------------------------------

    $start = Get-Date
    $end = $start.AddMinutes($minutes)

    $session = [ordered]@{
        id = [guid]::NewGuid().ToString()
        title = $title
        duration_minutes = $minutes
        start_time = $start.ToString("o")
        end_time = $end.ToString("o")
    }

    Save-ActiveFocus $session


    # ----------------------------------------
    # Start blocker
    # ----------------------------------------

    Start-FocusBlocker

    Stop-BlockedApplications


    # ----------------------------------------
    # Countdown
    # ----------------------------------------

    $previousCancelKeyPress = [Console]::CancelKeyPress

    $sessionStopped = $false

    while (-not $sessionStopped) {

        $script:FocusInterrupted = $false

        [Console]::CancelKeyPress = {
            param($cancelSender, $cancelEventArgs)
            $cancelEventArgs.Cancel = $true
            $script:FocusInterrupted = $true
        }

        while ($true) {

            if ($script:FocusInterrupted) {
                break
            }

            $now = Get-Date
            $remaining = $end - $now

            if ($remaining.TotalSeconds -le 0) {
                break
            }

            $hours = [math]::Floor($remaining.TotalHours)
            $minutesLeft = $remaining.Minutes
            $secondsLeft = $remaining.Seconds

            if ($hours -gt 0) {
                $display = "{0:D2}:{1:D2}:{2:D2}" -f $hours, $minutesLeft, $secondsLeft
            }
            else {
                $display = "{0:D2}:{1:D2}" -f $minutesLeft, $secondsLeft
            }

            Clear-Host

            Show-FocusBox `
                "FOCUS" `
                "$title`n`nTime remaining: $display`n`nPress Ctrl+C to request stopping the session." `
                "Cyan"

            Start-Sleep -Seconds 1
        }

        [Console]::CancelKeyPress = $previousCancelKeyPress

        if (-not $script:FocusInterrupted) {
            break
        }

        $answer = Read-Host "Stop focus session '$title'? (y/n)"

        if ($answer -notmatch "^(y|yes)$") {
            $script:FocusInterrupted = $false
            continue
        }

        $reason = Read-Host "Reason (optional)"

        if ([string]::IsNullOrWhiteSpace($reason)) {
            $reason = "Session stopped manually."
        }

        $actualEnd = Get-Date
        $actualMinutes = [math]::Floor(($actualEnd - $start).TotalMinutes)

        if ($actualMinutes -lt 0) {
            $actualMinutes = 0
        }

        $session.completed = $false
        $session.ended_at = $actualEnd.ToString("o")
        $session.actual_duration_minutes = $actualMinutes
        $session.reflection = $reason

        $history = @(Get-FocusHistory)
        $history += $session

        Save-FocusHistory $history
        Clear-ActiveFocus

        Clear-Host

        Show-FocusBox `
            "FOCUS STOPPED" `
            "$title`n`nFocused for $actualMinutes minutes.`n`nReason: $reason`n`nSession saved to history." `
            "Yellow"

        $sessionStopped = $true
    }

    if ($sessionStopped) {
        return
    }

    # ----------------------------------------
    # Session complete
    # ----------------------------------------

    Clear-Host

    Show-FocusNotification `
        "FOCUS COMPLETE" `
        "$title`n$minutes minutes completed."

    Show-FocusBox `
        "FOCUS COMPLETE" `
        "$title`n`n$minutes minutes completed." `
        "Green"

    Write-Host ""
    Write-Host "Notes (optional)" -ForegroundColor Cyan

    $reflection = Read-Host ">"

    if ([string]::IsNullOrWhiteSpace($reflection)) {
        $reflection = "No notes recorded."
    }


    # ----------------------------------------
    # Save history
    # ----------------------------------------

    $session.completed = $true
    $session.ended_at = (Get-Date).ToString("o")
    $session.reflection = $reflection

    $history = @(Get-FocusHistory)

    $history += $session

    Save-FocusHistory $history
    Clear-ActiveFocus

    Write-Host ""
    Write-Host "Focus session logged ✓" -ForegroundColor Green
    Write-Host ""
}


# ============================================
#                FOCUS HISTORY
# ============================================

function focushistory {

    $history = @(Get-FocusHistory)

    Clear-Host

    Write-Host ""
    Write-Host "FOCUS HISTORY" -ForegroundColor Cyan
    Write-Host "═════════════" -ForegroundColor DarkCyan
    Write-Host ""

    if ($history.Count -eq 0) {

        Write-Host "No focus sessions recorded yet." -ForegroundColor DarkGray
        Write-Host ""

        return
    }

    $recent = $history |
        Sort-Object {
            [datetime]::Parse($_.start_time)
        } -Descending |
        Select-Object -First 15

    foreach ($session in $recent) {

        $date = [datetime]::Parse($session.start_time)
        $duration = $session.duration_minutes

        if ($session.completed) {
            $symbol = "✓"
            $color = "Green"
        }
        else {
            $symbol = "✗"
            $color = "Yellow"
        }

        Write-Host "$($date.ToString('dd MMM'))  $($date.ToString('hh:mm tt'))  " -NoNewline -ForegroundColor DarkGray
        Write-Host "$($duration)m  " -NoNewline -ForegroundColor White
        Write-Host "$($session.title)" -NoNewline -ForegroundColor Cyan
        Write-Host "  $symbol" -ForegroundColor $color

        if ($session.reflection) {
            Write-Host "         $($session.reflection)" -ForegroundColor DarkGray
        }
    }

    Write-Host ""
}


# ============================================
#                 FOCUS STATS
# ============================================

function focusstats {

    $history = @(Get-FocusHistory)

    Clear-Host

    Write-Host ""
    Write-Host "FOCUS STATS" -ForegroundColor Cyan
    Write-Host "═══════════" -ForegroundColor DarkCyan
    Write-Host ""

    if ($history.Count -eq 0) {

        Write-Host "No focus data yet." -ForegroundColor DarkGray
        Write-Host ""

        return
    }

    $today = (Get-Date).Date
    $weekStart = $today.AddDays(
        -([int]$today.DayOfWeek)
    )

    $todaySessions = @(
        $history |
        Where-Object {
            ([datetime]::Parse($_.start_time)).Date -eq $today
        }
    )

    $weekSessions = @(
        $history |
        Where-Object {
            ([datetime]::Parse($_.start_time)) -ge $weekStart
        }
    )

    $todayMinutes = ($todaySessions |
        Measure-Object -Property duration_minutes -Sum).Sum

    $weekMinutes = ($weekSessions |
        Measure-Object -Property duration_minutes -Sum).Sum

    $completed = @(
        $history |
        Where-Object { $_.completed -eq $true }
    ).Count

    $total = $history.Count

    $rate = 0

    if ($total -gt 0) {
        $rate = [math]::Round(
            ($completed / $total) * 100
        )
    }

    Write-Host "Today" -ForegroundColor DarkGray
    Write-Host "  $todayMinutes minutes" -ForegroundColor White
    Write-Host ""

    Write-Host "This week" -ForegroundColor DarkGray
    Write-Host "  $weekMinutes minutes" -ForegroundColor White
    Write-Host ""

    Write-Host "Sessions" -ForegroundColor DarkGray
    Write-Host "  $total" -ForegroundColor White
    Write-Host ""

    Write-Host "Completed" -ForegroundColor DarkGray
    Write-Host "  $completed" -ForegroundColor Green
    Write-Host ""

    Write-Host "Completion rate" -ForegroundColor DarkGray
    Write-Host "  $rate%" -ForegroundColor Cyan
    Write-Host ""
}


# ============================================
#              FOCUS CONFIGURATION
# ============================================

function focusconfig {

    Clear-Host

    Write-Host ""
    Write-Host "FOCUS CONFIGURATION" -ForegroundColor Cyan
    Write-Host "═══════════════════" -ForegroundColor DarkCyan
    Write-Host ""

    Write-Host "Blocked applications:" -ForegroundColor White
    Write-Host ""

    $apps = Get-BlockedApplications

    foreach ($app in $apps) {
        Write-Host "  • $app" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Config file:" -ForegroundColor DarkGray
    Write-Host "  $FocusConfigFile" -ForegroundColor DarkGray
    Write-Host ""
}