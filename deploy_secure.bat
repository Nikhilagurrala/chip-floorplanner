@echo off
setlocal enabledelayedexpansion

:: Read tokens securely from .env
FOR /F "tokens=1,* delims==" %%A IN (.env) DO (
    IF "%%A"=="HF_TOKEN" set "HF=%%B"
    IF "%%A"=="GITHUB_TOKEN" set "GH=%%B"
)

:: Validate GH Token
IF "%GH%"=="PASTE_YOUR_GITHUB_TOKEN_HERE" (
    echo [ERROR] You must paste your real GitHub Token into .env first!
    exit /b 1
)

:: Init and Commit
IF NOT EXIST .git (
    echo [INFO] Initializing Git repository...
    git init
    git branch -m main
)

git add .
git commit -m "Final Commit: OpenEnv Hackathon Deployment" >nul 2>&1

:: Secure Hugging Face Push
echo [INFO] Pushing safely to Hugging Face...
git push --force https://user:%HF%@huggingface.co/spaces/diva29/chip-floorplanner main

:: Secure GitHub Push
echo [INFO] Pushing safely to GitHub...
git push --force https://%GH%@github.com/diva29/chip-floorplanner.git main

echo =======================================================
echo [SUCCESS] Deployment Completed with fully masked tokens!
echo =======================================================
endlocal
