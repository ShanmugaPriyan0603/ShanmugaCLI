# ============================================
#       SHANMUGA CLI - GOOGLE CALENDAR
# ============================================

$CalendarPython = "$HOME\ShanmugaCLI\google_calendar.py"


function cal {

    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    if (-not (Test-Path $CalendarPython)) {
        Write-Host ""
        Write-Host "Calendar backend not found." -ForegroundColor Red
        Write-Host ""
        Write-Host "Expected:" -ForegroundColor DarkGray
        Write-Host $CalendarPython -ForegroundColor Cyan
        Write-Host ""
        return
    }

    if ($Args.Count -eq 0) {
        python $CalendarPython "today"
        return
    }

    python $CalendarPython @Args
}