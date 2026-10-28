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
    if ($consoleWidth -lt 40) {
        $width = $consoleWidth
    }

    $innerWidth = [math]::Max(1, $width - 6)
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
    Write-Host "│  " -NoNewline -ForegroundColor DarkCyan
    Write-Host ((" " * $titleLeft) + $titleText + (" " * $titleRight)) -NoNewline -ForegroundColor $Color
    Write-Host "  │" -ForegroundColor DarkCyan
    Write-Host ("├" + ("─" * ($width - 2)) + "┤") -ForegroundColor DarkCyan

    foreach ($line in $lines) {
        $padding = $innerWidth - $line.Length
        Write-Host "│  " -NoNewline -ForegroundColor DarkCyan
        Write-Host $line -NoNewline -ForegroundColor White
        Write-Host ((" " * ($padding + 2)) + "│") -ForegroundColor DarkCyan
    }

    Write-Host ("╰" + ("─" * ($width - 2)) + "╯") -ForegroundColor DarkCyan
    Write-Host ""
}

function Clear-FocusScreen {
    try {
        Clear-Host -ErrorAction Stop
    }
    catch {
        # Non-interactive hosts do not always provide a console screen buffer.
    }
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

        $valid = @(
            foreach ($item in @($data)) {
                $start = ConvertTo-FocusDateTime $item.start_time
                $duration = 0
                if ($null -ne $item -and $null -ne $start -and
                    [int]::TryParse([string]$item.duration_minutes, [ref]$duration) -and
                    $duration -ge 0) {
                    $item
                }
            }
        )

        return $valid
    }
    catch {
        Write-Warning "Unable to read focus history: $($_.Exception.Message)"
        return @()
    }
}

function ConvertTo-FocusDateTime {

    param(
        $Value
    )

    if ($Value -is [datetime]) {
        return [datetime]$Value
    }

    $result = [datetime]::MinValue
    if ([datetime]::TryParse([string]$Value, [ref]$result)) {
        return $result
    }

    return $null
}

function Get-FocusSessionDuration {

    param(
        $Session
    )

    $actual = 0
    if ($null -ne $Session.actual_duration_minutes -and
        [int]::TryParse([string]$Session.actual_duration_minutes, [ref]$actual) -and
        $actual -ge 0) {
        return $actual
    }

    $planned = 0
    if ([int]::TryParse([string]$Session.duration_minutes, [ref]$planned) -and
        $planned -ge 0) {
        return $planned
    }

    return 0
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

        Clear-FocusScreen

        $durationLines = @()

        for ($i = 0; $i -lt $options.Count; $i++) {

            if ($i -eq $index) {
                $durationLines += ">  $($options[$i])"
            }
            else {
                $durationLines += "   $($options[$i])"
            }
        }

        $durationLines += ""
        $durationLines += "↑ / ↓   Select"
        $durationLines += "Enter   Confirm"

        Show-FocusBox `
            "FOCUS DURATION" `
            ($durationLines -join "`n") `
            "Cyan" `
            54

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

function Save-BlockedApplications {

    param(
        [string[]]$Applications
    )

    $config = @{
        blocked_apps = @(
            $Applications |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Sort-Object -Unique
        )
    }

    $config |
        ConvertTo-Json -Depth 5 |
        Set-Content $FocusConfigFile
}

function Get-FocusProgramCandidates {

    $candidates = @{}

    foreach ($process in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
        if (-not [string]::IsNullOrWhiteSpace($process.ExecutablePath)) {
            $candidates[$process.ExecutablePath] = [System.IO.Path]::GetFileName($process.ExecutablePath)
        }
    }

    $shortcutRoots = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
        "$env:USERPROFILE\Desktop",
        "$env:PUBLIC\Desktop"
    )

    try {
        $shell = New-Object -ComObject WScript.Shell
        foreach ($shortcut in @(
            Get-ChildItem -Path $shortcutRoots -Filter *.lnk -File -Recurse -ErrorAction SilentlyContinue
        )) {
            $target = $shell.CreateShortcut($shortcut.FullName).TargetPath
            if ($target -and $target.EndsWith(".exe", [System.StringComparison]::OrdinalIgnoreCase)) {
                $candidates[$target] = $shortcut.BaseName
            }
        }
    }
    catch {
        # Running-process entries remain available if shortcut inspection is unavailable.
    }

    return @(
        $candidates.GetEnumerator() |
        ForEach-Object {
            [pscustomobject]@{
                Name = $_.Value
                Path = $_.Key
            }
        } |
        Sort-Object Name, Path
    )
}

function Get-FocusBlockCandidates {

    param(
        [ValidateSet("Program", "Batch", "Folder")]
        [string]$Type
    )

    if ($Type -eq "Program") {
        return @(Get-FocusProgramCandidates)
    }

    $extensions = if ($Type -eq "Batch") { @("*.bat", "*.cmd") } else { @("*") }
    $roots = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
        "$env:USERPROFILE\Desktop",
        "$env:PUBLIC\Desktop",
        "$env:USERPROFILE\Downloads",
        "$env:USERPROFILE\Documents"
    )
    $candidates = @()

    foreach ($root in $roots) {
        if (-not (Test-Path $root -PathType Container)) {
            continue
        }

        if ($Type -eq "Folder") {
            $candidates += Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue
        }
        else {
            foreach ($extension in $extensions) {
                $candidates += Get-ChildItem -Path $root -Filter $extension -File -Recurse -ErrorAction SilentlyContinue
            }
        }
    }

    return @(
        $candidates |
        Sort-Object FullName -Unique |
        ForEach-Object {
            [pscustomobject]@{
                Name = $_.Name
                Path = $_.FullName
            }
        }
    )
}

function Add-FocusBlockedApplication {

    Write-Host "1. Program (.exe)" -ForegroundColor White
    Write-Host "2. Batch file (.bat or .cmd)" -ForegroundColor White
    Write-Host "3. Folder" -ForegroundColor White
    $typeChoice = (Read-Host "What should be blocked? (1-3)").Trim()

    $type = switch ($typeChoice) {
        "1" { "Program" }
        "2" { "Batch" }
        "3" { "Folder" }
        default { return }
    }

    $query = Read-Host "Search $($type.ToLower())s (name or path)"
    if ([string]::IsNullOrWhiteSpace($query)) {
        return
    }

    $programMatches = @(
        Get-FocusBlockCandidates -Type $type |
        Where-Object {
            $_.Name.IndexOf($query, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or
            $_.Path.IndexOf($query, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        } |
        Select-Object -First 30
    )

    if ($programMatches.Count -eq 0) {
        Write-Host "No match found. Enter a full path instead? (y/n)" -ForegroundColor Yellow
        if ((Read-Host) -match "^(y|yes)$") {
            $manualPath = (Read-Host "Path").Trim().Trim('"')
            $pathType = if ($type -eq "Folder") { "Container" } else { "Leaf" }
            $validBatch = $type -eq "Batch" -and
                [System.IO.Path]::GetExtension($manualPath) -in @(".bat", ".cmd")
            $validProgram = $type -eq "Program" -and
                [System.IO.Path]::GetExtension($manualPath) -eq ".exe"
            if ($manualPath -and (Test-Path $manualPath -PathType $pathType) -and
                ($type -eq "Folder" -or $validBatch -or $validProgram)) {
                $programMatches = @([pscustomobject]@{
                    Name = [System.IO.Path]::GetFileName($manualPath)
                    Path = $manualPath
                })
            }
        }
    }

    if ($programMatches.Count -eq 0) {
        Write-Host "No program was added." -ForegroundColor DarkGray
        return
    }

    Write-Host ""
    for ($i = 0; $i -lt $programMatches.Count; $i++) {
        Write-Host ("  {0}. {1}  {2}" -f ($i + 1), $programMatches[$i].Name, $programMatches[$i].Path) -ForegroundColor White
    }

    $choice = 0
    if (-not [int]::TryParse((Read-Host "Choose a program (0 to cancel)"), [ref]$choice) -or
        $choice -lt 1 -or $choice -gt $programMatches.Count) {
        return
    }

    $selected = $programMatches[$choice - 1].Path
    $apps = @(Get-BlockedApplications)
    if ($apps -contains $selected) {
        Write-Host "That program is already blocked." -ForegroundColor Yellow
        return
    }

    Save-BlockedApplications ($apps + $selected)
    Write-Host "$($programMatches[$choice - 1].Name) added to the focus blacklist." -ForegroundColor Green
}

function Remove-FocusBlockedApplication {

    $apps = @(Get-BlockedApplications)
    if ($apps.Count -eq 0) {
        Write-Host "The focus blacklist is empty." -ForegroundColor DarkGray
        return
    }

    for ($i = 0; $i -lt $apps.Count; $i++) {
        Write-Host ("  {0}. {1}" -f ($i + 1), $apps[$i]) -ForegroundColor Yellow
    }

    $choice = 0
    if (-not [int]::TryParse((Read-Host "Remove which program (0 to cancel)"), [ref]$choice) -or
        $choice -lt 1 -or $choice -gt $apps.Count) {
        return
    }

    $remaining = @(
        for ($i = 0; $i -lt $apps.Count; $i++) {
            if ($i -ne ($choice - 1)) {
                $apps[$i]
            }
        }
    )

    Save-BlockedApplications $remaining
    Write-Host "Blacklist entry removed." -ForegroundColor Green
}


function Stop-BlockedApplications {

    $apps = @(Get-BlockedApplications)
    $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)

    foreach ($app in $apps) {
        $target = [string]$app
        $targetFullPath = $null
        try {
            $targetFullPath = [System.IO.Path]::GetFullPath($target).TrimEnd("\")
        }
        catch {
            continue
        }

        $targetName = [System.IO.Path]::GetFileName($target)
        $targetProcessName = [System.IO.Path]::GetFileNameWithoutExtension($target)
        $isFolder = (Test-Path $target -PathType Container) -or
            $target.EndsWith("\") -or $target.EndsWith("/")
        $isBatch = [System.IO.Path]::GetExtension($target) -in @(".bat", ".cmd")

        $matches = @(
            $processes | Where-Object {
                $exe = [string]$_.ExecutablePath
                $command = [string]$_.CommandLine
                if ($isFolder) {
                    ($exe -and $exe.StartsWith("$targetFullPath\", [System.StringComparison]::OrdinalIgnoreCase)) -or
                    ($command -and $command.IndexOf("$targetFullPath\", [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
                }
                elseif ($isBatch) {
                    $command -and (
                        $command.IndexOf($target, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or
                        $command.IndexOf($targetFullPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
                    )
                }
                else {
                    ($exe -and (
                        $exe.Equals($targetFullPath, [System.StringComparison]::OrdinalIgnoreCase) -or
                        [System.IO.Path]::GetFileName($exe).Equals($targetName, [System.StringComparison]::OrdinalIgnoreCase)
                    )) -or
                    (!$exe -and $_.Name -and $_.Name.Equals($targetName, [System.StringComparison]::OrdinalIgnoreCase))
                }
            }
        )

        $ids = @($matches | ForEach-Object { [int]$_.ProcessId })
        $changed = $true
        while ($changed) {
            $changed = $false
            foreach ($process in $processes) {
                if ($ids -contains [int]$process.ParentProcessId -and
                    $ids -notcontains [int]$process.ProcessId) {
                    $ids += [int]$process.ProcessId
                    $changed = $true
                }
            }
        }

        foreach ($id in ($ids | Sort-Object -Unique)) {
            Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
        }
    }
}


# ============================================
#             BLOCKER MONITOR
# ============================================

    function Start-FocusBlocker {

    $script = @"
    while (Test-Path '$FocusStateFile') {
        try {
            \$state = Get-Content '$FocusStateFile' -Raw | ConvertFrom-Json
            \$end = [datetime]::MinValue
            if (-not [datetime]::TryParse([string]\$state.end_time, [ref]\$end) -or (Get-Date) -ge \$end) {
                break
            }

            # Recheck frequently so newly launched blocked processes are terminated quickly.
            \$apps = @(Get-Content '$FocusConfigFile' -Raw | ConvertFrom-Json).blocked_apps
            \$processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
            foreach (\$app in @(\$apps)) {
                \$target = [string]\$app
                \$full = [System.IO.Path]::GetFullPath(\$target).TrimEnd('\')
                \$name = [System.IO.Path]::GetFileName(\$target)
                \$folder = (Test-Path \$target -PathType Container) -or \$target.EndsWith('\') -or \$target.EndsWith('/')
                \$batch = [System.IO.Path]::GetExtension(\$target) -in @('.bat', '.cmd')
                \$matches = \$processes | Where-Object {
                    \$exe = [string]\$_.ExecutablePath
                    \$cmd = [string]\$_.CommandLine
                    if (\$folder) {
                        (\$exe -and \$exe.StartsWith("\$full\", [System.StringComparison]::OrdinalIgnoreCase)) -or
                        (\$cmd -and \$cmd.IndexOf("\$full\", [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
                    } elseif (\$batch) {
                        \$cmd -and (\$cmd.IndexOf(\$target, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -or \$cmd.IndexOf(\$full, [System.StringComparison]::OrdinalIgnoreCase) -ge 0)
                    } else {
                        (\$exe -and [System.IO.Path]::GetFileName(\$exe).Equals(\$name, [System.StringComparison]::OrdinalIgnoreCase)) -or
                        (!\$exe -and \$_.Name -and \$_.Name.Equals(\$name, [System.StringComparison]::OrdinalIgnoreCase))
                    }
                }
                foreach (\$process in \$matches) {
                    Stop-Process -Id \$process.ProcessId -Force -ErrorAction SilentlyContinue
                }
            }
        } catch {
            # Retry on the next pass while the focus session remains active.
        }
        Start-Sleep -Milliseconds 250
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
    $endedAt = Get-Date
    $session | Add-Member -NotePropertyName "ended_at" -NotePropertyValue $endedAt.ToString("o") -Force
    $startedAt = ConvertTo-FocusDateTime $session.start_time
    $actualMinutes = 0
    if ($null -ne $startedAt) {
        $actualMinutes = [math]::Max(0, [math]::Floor(($endedAt - $startedAt).TotalMinutes))
    }
    $session | Add-Member -NotePropertyName "actual_duration_minutes" -NotePropertyValue $actualMinutes -Force
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
        "focus                  Start a focus session`nfocus status           Show the active session and remaining time`nfocus stop             Stop the active focus session`nfocus delete           Delete all saved focus history`nfocus history          View recent focus sessions`nfocus stats            View focus statistics`nfocus settings         Manage the blacklist of programs, batch files, and folders`nfocus config           Open focus settings (compatibility alias)`nfocus help             Show this complete command list`n`nSettings menu:`n1  Add a program, batch file, or folder`n2  Remove a blacklist entry`n3  Refresh the blacklist`n4  Done`n`nDuring focus mode, blacklisted programs and processes from blacklisted folders are stopped automatically." `
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

            "settings" {
                focusconfig
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

    Clear-FocusScreen

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

            Clear-FocusScreen

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

        Clear-FocusScreen

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

    Clear-FocusScreen

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

    Clear-FocusScreen

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
            ConvertTo-FocusDateTime $_.start_time
        } -Descending |
        Select-Object -First 15

    foreach ($session in $recent) {

        $date = ConvertTo-FocusDateTime $session.start_time
        if ($null -eq $date) {
            continue
        }
        $duration = Get-FocusSessionDuration $session

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

        if (-not [string]::IsNullOrWhiteSpace([string]$session.reflection)) {
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

    Clear-FocusScreen

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

    $todayMinutes = 0
    $weekMinutes = 0
    foreach ($session in $history) {
        $start = ConvertTo-FocusDateTime $session.start_time
        if ($null -eq $start) {
            continue
        }

        $duration = Get-FocusSessionDuration $session
        if ($start.Date -eq $today) {
            $todayMinutes += $duration
        }
        if ($start -ge $weekStart) {
            $weekMinutes += $duration
        }
    }

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

    while ($true) {

        Clear-FocusScreen
        $apps = @(Get-BlockedApplications)
        $blacklist = if ($apps.Count -gt 0) {
            ($apps | ForEach-Object {
                $kind = if (Test-Path $_ -PathType Container) {
                    "Folder"
                }
                elseif ([System.IO.Path]::GetExtension($_) -in @(".bat", ".cmd")) {
                    "Batch"
                }
                else {
                    "Program"
                }
                "• [$kind] $_"
            }) -join "`n"
        }
        else {
            "No distracting programs are blocked."
        }

        Show-FocusBox `
            "FOCUS SETTINGS" `
            "Blacklist targets blocked while focus mode is active:`n`n$blacklist`n`n1  Add a distracting program, batch file, or folder`n2  Remove a blacklist entry`n3  Refresh blacklist`n4  Done`n`nConfig file: $FocusConfigFile" `
            "Cyan"

        $choice = (Read-Host "Choose an option").Trim()
        switch ($choice) {
            "1" {
                Add-FocusBlockedApplication
                Read-Host "Press Enter to continue" | Out-Null
            }
            "2" {
                Remove-FocusBlockedApplication
                Read-Host "Press Enter to continue" | Out-Null
            }
            "3" {
                continue
            }
            "4" {
                return
            }
            default {
                Write-Host "Choose 1, 2, 3, or 4." -ForegroundColor Yellow
                Start-Sleep -Seconds 1
            }
        }
    }
}
