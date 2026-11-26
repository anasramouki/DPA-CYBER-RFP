@echo off
title Assistant d'Installation CyberRFP Maroc - DataProtech
cd /d "%~dp0"

echo ==============================================================================
echo        CYBERRFP MAROC — ASSISTANT D'INSTALLATION WINDOWS
echo              ENTREPRISE : DataProtech company (DPA)
echo                  DOMAINE : @dpg-cyber.com
echo ==============================================================================
echo.
echo Lancement de l'assistant d'installation graphique (Next -> Next -> Finish)...

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\Setup_Wizard.ps1"
