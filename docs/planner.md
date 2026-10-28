# Study Tracker and Day Planner

The planner is local-first. `planner` stores JSON under `planner/data`, validates schedules locally, and only uses Gemini when explicitly requested by an integration that supplies an API key.

## Setup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-planner.txt
$env:GEMINI_API_KEY = "your-key" # session-only; never commit this
```

For persistent local configuration, create `planner\.env.local` with this format:

```text
GEMINI_API_KEY=your-key
```

The planner reads that file automatically when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is not already set. The file is intentionally ignored by Git. Environment variables take precedence over the local file.

`GEMINI_MODEL` optionally selects the model; the default is `gemini-3.8-flash`. `GOOGLE_API_KEY` is accepted as a fallback.

## PowerShell commands

For shorter commands, load [planner.ps1](../planner.ps1) into your PowerShell profile. It provides `study-planner`, `day-planner`, and `planner help`.

```powershell
# Direct wrapper usage
.\studyplanner.ps1 help
.\studyplanner.ps1 subjects
.\studyplanner.ps1 ask "I have a DTSP exam on 2026-11-01. I finished units 1 and 2, and I feel anxious."
.\studyplanner.ps1 add-subject "Digital Systems"
.\studyplanner.ps1 add-task <subject-id>
.\studyplanner.ps1 log 45
.\studyplanner.ps1 progress
.\studyplanner.ps1 export > planner-export.json
.\studyplanner.ps1 import planner-export.json
.\dayplanner.ps1 help
.\dayplanner.ps1 preferences
.\dayplanner.ps1 add
.\dayplanner.ps1 plan 2026-10-26
.\dayplanner.ps1 plan --ai 2026-10-26
.\dayplanner.ps1 now
.\dayplanner.ps1 next

# After loading planner.ps1
study-planner subjects
study-planner ask "I have a DTSP exam on 2026-11-01. I finished units 1 and 2."
day-planner plan
planner help
```

`study-planner ask` sends the free-form message to Gemini as a structured extraction request. The response is returned as formatted JSON with subjects, exam dates, unit statuses, feelings, estimated effort, derived remaining units, days/hours left, tasks, assumptions, and missing details. The local code derives counts and time-left values rather than trusting model arithmetic. The command asks for confirmation before merging subjects and tasks into JSON storage.

Planning always previews changes and asks `Apply these changes? [y/N]`. Enter means reject. Fixed commitments are preserved and validation errors prevent saving. `day plan --ai` requires `GEMINI_API_KEY`, requests a structured proposal, and validates it locally before the same preview. Without `--ai`, the deterministic local scheduler works without network access.

`day done ID`, `day skip ID`, `day edit ID`, and `day delete ID` update approved schedule blocks. Deletion requires an explicit confirmation.

## Data and recovery

The JSON files are independent and use stable IDs. Important saves create timestamped `.backup-*.json` files. Corrupt input is retained as `.corrupt-*.json` and reported instead of being overwritten. Copy a backup over the corresponding JSON file to restore it.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The core scheduler works without a Gemini key. Gemini calls must be mocked in tests and must never receive secrets in prompts beyond the minimum planning context.

## Add the commands to `$PROFILE`

Check the profile path:

```powershell
$PROFILE
```

Open or create it:

```powershell
New-Item -ItemType File -Path $PROFILE -Force | Out-Null
notepad $PROFILE
```

Add this line, using the actual repository path:

```powershell
. "C:\Users\shanm\ShanmugaCLI\planner.ps1"
```

Reload the profile and verify:

```powershell
. $PROFILE
planner help
study-planner help
day-planner help
```

The loader uses the repository's `.venv` Python interpreter and does not permanently modify `PATH` or environment variables.
