@echo off
title Assistant d'Installation CyberRFP Maroc - DataProtech
cd /d "%~dp0"

echo ==============================================================================
echo        CYBERRFP MAROC — ASSISTANT D'INSTALLATION WINDOWS
echo              ENTREPRISE : DataProtech company (DPA)
echo                  DOMAINE : @dpg-cyber.com
echo ==============================================================================
echo.
echo Lancement de l'assistant d'installation graphique...

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup_Wizard.ps1"
