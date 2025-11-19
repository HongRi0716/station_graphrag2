# PowerShell script to check for large files before git operations
# Usage: .\scripts\prevent-large-files.ps1

$MAX_FILE_SIZE = 10MB  # 10MB limit
$largeFiles = @()

Write-Host "Checking for large files..." -ForegroundColor Yellow

# Get staged files
$stagedFiles = git diff --cached --name-only --diff-filter=ACM 2>$null
if (-not $stagedFiles) {
    # If no staged files, check all tracked files
    $stagedFiles = git ls-files
}

foreach ($file in $stagedFiles) {
    if (Test-Path $file) {
        $fileInfo = Get-Item $file -ErrorAction SilentlyContinue
        if ($fileInfo -and $fileInfo.Length -gt $MAX_FILE_SIZE) {
            $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
            $largeFiles += [PSCustomObject]@{
                File = $file
                Size = "$sizeMB MB"
            }
        }
    }
}

if ($largeFiles.Count -gt 0) {
    Write-Host "`nError: Large files detected!" -ForegroundColor Red
    Write-Host "The following files exceed 10MB:" -ForegroundColor Yellow
    $largeFiles | Format-Table -AutoSize
    Write-Host "`nPlease:" -ForegroundColor Yellow
    Write-Host "  1. Remove these files from staging: git reset HEAD <file>"
    Write-Host "  2. Add them to .gitignore if they should not be tracked"
    Write-Host "  3. Use Git LFS for large files that need version control"
    exit 1
}

Write-Host "No large files detected." -ForegroundColor Green
exit 0

