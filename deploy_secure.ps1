param(
    [string]$hfRepo = "diva29/chip-floorplanner",
    [string]$ghRepo = "diva29/chip-floorplanner"
)

# Parse .env (extracts masked passwords into memory momentarily)
$envContent = Get-Content ".env"
$hfToken = $null
$ghToken = $null

foreach ($line in $envContent) {
    if ($line -match "^HF_TOKEN=(.*)$") { $hfToken = $matches[1] }
    if ($line -match "^GITHUB_TOKEN=(.*)$") { $ghToken = $matches[1] }
}

if (-not $hfToken) {
    Write-Host "Error: HF_TOKEN not found in .env" -ForegroundColor Red
    exit 1
}

# Ensure Git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Cyan
    git init
    git branch -m main
}

# Stage and commit everything
Write-Host "Committing project files..." -ForegroundColor Cyan
git add .
try {
    git commit -m "Initial commit: OpenEnv Hackathon Submission Final"
} catch {
    # If no changes are present, git commit throws an error. We can ignore it safely.
}

# Hugging Face Deploy
Write-Host "Deploying to Hugging Face Spaces ($hfRepo)..." -ForegroundColor Cyan
$hfUrl = "https://user:$hfToken@huggingface.co/spaces/$hfRepo"
git push --force $hfUrl main

# GitHub Deploy
if ($ghToken -and $ghToken -ne "PASTE_YOUR_GITHUB_TOKEN_HERE") {
    Write-Host "Deploying to GitHub ($ghRepo)..." -ForegroundColor Cyan
    $ghUrl = "https://$ghToken@github.com/$ghRepo.git"
    git push --force $ghUrl main
} else {
    Write-Host "GitHub deployment skipped: Insert your real GITHUB_TOKEN in .env first." -ForegroundColor Yellow
}

Write-Host "`nDeployment Routine Complete!" -ForegroundColor Green
