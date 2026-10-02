# ============================================
#              SHANMUGA CLI POWER
# ============================================

function Show-PowerBox {

    param(
        [string]$Title,
        [string]$Message,
        [ConsoleColor]$Color = "Cyan"
    )

    $width = 56
    $innerWidth = $width - 4

    Write-Host ""
    Write-Host ("╭" + ("─" * ($width - 2)) + "╮") -ForegroundColor DarkMagenta

    if ($Title.Length -gt $innerWidth) {
        $Title = $Title.Substring(0, $innerWidth - 3) + "..."
    }

    $padding = $innerWidth - $Title.Length
    $left = [math]::Floor($padding / 2)
    $right = $padding - $left

    Write-Host ("│ " + (" " * $left) + $Title + (" " * $right) + " │") -ForegroundColor $Color
    Write-Host ("├" + ("─" * ($width - 2)) + "┤") -ForegroundColor DarkMagenta

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

    Write-Host ("╰" + ("─" * ($width - 2)) + "╯") -ForegroundColor DarkMagenta
    Write-Host ""
}


# ============================================
#              CANCEL POWER ACTION
# ============================================

function cancelpower {

    $cancelled = $false

    # ----------------------------------------
    # Cancel shutdown / restart
    # ----------------------------------------

    shutdown.exe /a 2>$null

    if ($LASTEXITCODE -eq 0) {
        $cancelled = $true
    }

    # ----------------------------------------
    # Cancel scheduled hibernation
    # ----------------------------------------

    $taskName = "ShanmugaCLI-Hibernate"

    $task = Get-ScheduledTask `
        -TaskName $taskName `
        -ErrorAction SilentlyContinue

    if ($task) {

        Unregister-ScheduledTask `
            -TaskName $taskName `
            -Confirm:$false `
            -ErrorAction SilentlyContinue

        $cancelled = $true
    }

    # ----------------------------------------
    # Result
    # ----------------------------------------

    if ($cancelled) {

        Show-PowerBox `
            "POWER ACTION CANCELLED" `
            "Any scheduled shutdown, restart, or hibernation has been cancelled." `
            "Green"

    }
    else {

        Show-PowerBox `
            "NOTHING SCHEDULED" `
            "There was no scheduled shutdown, restart, or hibernation." `
            "Yellow"
    }
}


# ============================================
#              SHUTDOWN
# ============================================

function shutdown {

    param(
        [int]$Minutes
    )

    # Timed shutdown
    if ($Minutes -gt 0) {

        $seconds = $Minutes * 60

        shutdown.exe /s /t $seconds /c "Shanmuga CLI scheduled shutdown"

        $time = (Get-Date).AddMinutes($Minutes)

        Show-PowerBox `
            "SHUTDOWN SCHEDULED" `
            "Shutdown in $Minutes minutes.`n`nScheduled for $($time.ToString('hh:mm tt'))`n`nUse 'cancelpower' to cancel." `
            "Yellow"

        return
    }


    # Immediate shutdown
    $answer = Read-Host "Shut down the computer now? (y/n)"

    if ($answer -match "^(y|yes)$") {

        Show-PowerBox `
            "SHUTTING DOWN" `
            "Your computer will shut down now." `
            "Red"

        Start-Sleep -Seconds 1

        shutdown.exe /s /t 0

    }
    else {

        Write-Host ""
        Write-Host "Shutdown cancelled." -ForegroundColor DarkGray
        Write-Host ""
    }
}


# ============================================
#                RESTART
# ============================================

function restart {

    param(
        [int]$Minutes
    )

    # Timed restart
    if ($Minutes -gt 0) {

        $seconds = $Minutes * 60

        shutdown.exe /r /t $seconds /c "Shanmuga CLI scheduled restart"

        $time = (Get-Date).AddMinutes($Minutes)

        Show-PowerBox `
            "RESTART SCHEDULED" `
            "Restart in $Minutes minutes.`n`nScheduled for $($time.ToString('hh:mm tt'))`n`nUse 'cancelpower' to cancel." `
            "Yellow"

        return
    }


    # Immediate restart
    $answer = Read-Host "Restart the computer now? (y/n)"

    if ($answer -match "^(y|yes)$") {

        Show-PowerBox `
            "RESTARTING" `
            "Your computer will restart now." `
            "Yellow"

        Start-Sleep -Seconds 1

        shutdown.exe /r /t 0

    }
    else {

        Write-Host ""
        Write-Host "Restart cancelled." -ForegroundColor DarkGray
        Write-Host ""
    }
}


# ============================================
#                HIBERNATE
# ============================================

function hibernate {

    param(
        [int]$Minutes
    )

    # Timed hibernate
    if ($Minutes -gt 0) {

        $time = (Get-Date).AddMinutes($Minutes)

        # Windows Task Scheduler handles delayed hibernation.
        $taskName = "ShanmugaCLI-Hibernate"

        # Remove an older task if one exists.
        schtasks.exe /delete `
            /tn $taskName `
            /f 2>$null | Out-Null

        $runTime = $time.ToString("HH:mm")

        $date = $time.ToString("MM/dd/yyyy")
        $action = 'rundll32.exe powrprof.dll,SetSuspendState Hibernate'

        schtasks.exe /create `
            /tn $taskName `
            /tr $action `
            /sc once `
            /st $runTime `
            /sd $date `
            /f | Out-Null

        Show-PowerBox `
            "HIBERNATION SCHEDULED" `
            "Hibernate in $Minutes minutes.`n`nScheduled for $($time.ToString('hh:mm tt'))`n`nUse 'cancelpower' to cancel." `
            "Cyan"

        return
    }

    # Immediate hibernate
    $answer = Read-Host "Hibernate the computer now? (y/n)"

    if ($answer -match "^(y|yes)$") {

        Show-PowerBox `
            "HIBERNATING" `
            "Your computer will hibernate now." `
            "Cyan"

        Start-Sleep -Seconds 1

        rundll32.exe powrprof.dll,SetSuspendState Hibernate

    }
    else {

        Write-Host ""
        Write-Host "Hibernation cancelled." -ForegroundColor DarkGray
        Write-Host ""
    }
}


# ============================================
#                  POWER
# ============================================

function power {

    Clear-Host

    Show-PowerBox `
        "POWER STATUS" `
        "Available commands:`n`n  shutdown       Shut down now`n  shutdown 30    Shut down in 30 minutes`n  restart        Restart now`n  restart 30     Restart in 30 minutes`n  hibernate      Hibernate now`n  hibernate 30   Hibernate in 30 minutes`n  cancelpower    Cancel scheduled power action" `
        "Magenta"
}