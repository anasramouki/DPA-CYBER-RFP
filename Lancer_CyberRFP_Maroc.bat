@echo off
title CyberRFP Maroc - Lanceur
cd /d "%~dp0"

echo ==============================================================================
echo        CYBERRFP MAROC — VEILLE MARCHES PUBLICS CYBERSECURITE
echo                  ENTREPRISE : DPA (ICE: 003102490000030)
echo ==============================================================================
echo.

if exist "CyberRFP-Maroc.exe" (
    echo Demarrage de l'executable autonome...
    start "" "CyberRFP-Maroc.exe"
) else if exist "dist\CyberRFP-Maroc.exe" (
    echo Demarrage de l'executable autonome...
    start "" "dist\CyberRFP-Maroc.exe"
) else (
    echo Demarrage via Python...
    python desktop_launcher.py
)
