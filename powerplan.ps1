# ============================================================
# ShanmugaCLI - Power Plan Manager
# ============================================================

$PowerPlans = @{
    "balanced" = @{
        Name = "Balanced"
        Guid = "381b4222-f694-41f0-9685-ff5bb260df2e"
    }

    "downloading" = @{
        Name = "Downloading..."
        Guid = "dc285110-d4c8-408c-89d1-65645eed3599"
    }
}


function Get-ActivePowerPlan {

    $output = powercfg /getactivescheme 2>$null

    if ($output -match "GUID:\s+([a-fA-F0-9-]+)\s+\((.+?)\)") {
        return @{
            Guid = $matches[1]
            Name = $matches[2]
        }
    }

    return $null
}


function Show-PowerPlanBox {

    param(
        [string]$Title,
        [string[]]$Lines
    )

        $width = 56
        $innerWidth = $width - 4

    Write-Host ""

        Write-Host ("╭" + ("─" * ($width - 2)) + "╮") -ForegroundColor DarkGray

    # Center title.
        if ($Title.Length -gt $innerWidth) {
            $Title = $Title.Substring(0, $innerWidth - 3) + "..."
        }

    $titleLeft = [math]::Floor(($innerWidth - $Title.Length) / 2)
    $titleRight = $innerWidth - $Title.Length - $titleLeft

        Write-Host "│ " -NoNewline -ForegroundColor DarkGray
    Write-Host (" " * $titleLeft) -NoNewline
    Write-Host $Title -NoNewline -ForegroundColor Magenta
    Write-Host (" " * $titleRight) -NoNewline
        Write-Host " │" -ForegroundColor DarkGray

        Write-Host ("├" + ("─" * ($width - 2)) + "┤") -ForegroundColor DarkGray

        foreach ($rawLine in $Lines) {
            if ([string]::IsNullOrWhiteSpace($rawLine)) {
                $wrappedLines = @("" )
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

                Write-Host "│ " -NoNewline -ForegroundColor DarkGray
                Write-Host $line -NoNewline -ForegroundColor White
                Write-Host ((" " * $padding) + " │") -ForegroundColor DarkGray
            }
    }

        Write-Host ("╰" + ("─" * ($width - 2)) + "╯") -ForegroundColor DarkGray

    Write-Host ""
}


function Show-PowerPlans {

    $active = Get-ActivePowerPlan

    $lines = @()

    foreach ($key in $PowerPlans.Keys) {

        $plan = $PowerPlans[$key]

        if ($active -and $active.Guid -eq $plan.Guid) {
            $lines += "●  $($plan.Name)  [ACTIVE]"
        }
        else {
            $lines += "○  $($plan.Name)"
        }
    }

    Show-PowerPlanBox -Title "POWER PLANS" -Lines $lines
}


function Set-ShanmugaPowerPlan {

    param(
        [string]$Plan
    )

    if (-not $PowerPlans.ContainsKey($Plan)) {

        Show-PowerPlanBox `
            -Title "POWER PLANS" `
            -Lines @(
                "Unknown power plan: $Plan"
                ""
                "Available:"
                "  balanced"
                "  downloading"
            )

        return
    }

    $selected = $PowerPlans[$Plan]

    $active = Get-ActivePowerPlan

    if ($active -and $active.Guid -eq $selected.Guid) {

        Show-PowerPlanBox `
            -Title "POWER PLANS" `
            -Lines @(
                "Already active"
                ""
                "$($selected.Name)"
            )

        return
    }

    powercfg /setactive $selected.Guid

    Start-Sleep -Milliseconds 300

    $newActive = Get-ActivePowerPlan

    if ($newActive -and $newActive.Guid -eq $selected.Guid) {

        Show-PowerPlanBox `
            -Title "POWER PLANS" `
            -Lines @(
                "Power plan switched"
                ""
                "→  $($selected.Name)"
            )
    }
    else {

        Show-PowerPlanBox `
            -Title "POWER PLANS" `
            -Lines @(
                "Failed to switch power plan"
                ""
                "$($selected.Name)"
            )
    }
}


function Invoke-PowerPlan {

    param(
        [string]$Command
    )

    if (-not $Command) {

        Show-PowerPlans
        return
    }

    switch ($Command.ToLower()) {

        "list" {
            Show-PowerPlans
        }

        "current" {

            $active = Get-ActivePowerPlan

            if ($active) {
                Show-PowerPlanBox `
                    -Title "CURRENT POWER PLAN" `
                    -Lines @(
                        $active.Name
                        ""
                        $active.Guid
                    )
            }
        }

        "balanced" {
            Set-ShanmugaPowerPlan "balanced"
        }

        "downloading" {
            Set-ShanmugaPowerPlan "downloading"
        }

        default {
            Set-ShanmugaPowerPlan $Command.ToLower()
        }
    }
}