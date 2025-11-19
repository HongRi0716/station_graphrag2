# PowerShell script to remove large files from Git tracking
# Usage: .\scripts\remove-large-files-from-git.ps1 [file_path]

param(
    [Parameter(Mandatory=$false)]
    [string]$FilePath = ""
)

$MAX_FILE_SIZE = 10MB

Write-Host "Finding large files in Git repository..." -ForegroundColor Yellow

if ($FilePath) {
    # Remove specific file
    if (Test-Path $FilePath) {
        Write-Host "Removing '$FilePath' from Git tracking..." -ForegroundColor Yellow
        git rm --cached $FilePath
        Write-Host "File removed from Git. Don't forget to:" -ForegroundColor Green
        Write-Host "  1. Add it to .gitignore if not already there"
        Write-Host "  2. Commit the change: git commit -m 'Remove large file from tracking'"
    } else {
        Write-Host "Error: File not found: $FilePath" -ForegroundColor Red
        exit 1
    }
} else {
    # Find and list large files
    $largeFiles = git ls-files | ForEach-Object {
        try {
            $item = Get-Item $_ -ErrorAction Stop
            if ($item.Length -gt $MAX_FILE_SIZE) {
                [PSCustomObject]@{
                    File = $_
                    Size = [math]::Round($item.Length / 1MB, 2)
                }
            }
        } catch {
            # Skip files that don't exist or can't be accessed
        }
    } | Sort-Object Size -Descending

    if ($largeFiles.Count -eq 0) {
        Write-Host "No large files found in Git repository." -ForegroundColor Green
        exit 0
    }

    Write-Host "`nFound the following large files:" -ForegroundColor Yellow
    $largeFiles | Format-Table -AutoSize

    Write-Host "`nTo remove a file from Git tracking, run:" -ForegroundColor Cyan
    Write-Host "  .\scripts\remove-large-files-from-git.ps1 -FilePath 'path/to/file'`n" -ForegroundColor Cyan

    # Check if files are in .gitignore
    Write-Host "Checking if files are in .gitignore..." -ForegroundColor Yellow
    foreach ($file in $largeFiles) {
        $ignored = git check-ignore -v $file.File 2>$null
        if ($ignored) {
            Write-Host "  ✓ $($file.File) is in .gitignore" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $($file.File) is NOT in .gitignore" -ForegroundColor Red
        }
    }
}

