@echo off
chcp 65001 >nul
title CyberRFP Maroc - Configuration Acces iPhone / Reseau Local

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Demande d'elevation administrateur pour configurer le pare-feu Windows...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo    CyberRFP Maroc - Autorisation du Port 8000 (Pare-feu Windows)
echo ======================================================================
echo.
echo Configuration de la regle de pare-feu pour autoriser l'acces depuis
echo votre iPhone / smartphone et laptop connectes au meme reseau Wi-Fi...
echo.

netsh advfirewall firewall delete rule name="CyberRFP Maroc (Port 8000)" >nul 2>&1
netsh advfirewall firewall add rule name="CyberRFP Maroc (Port 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any

for /f "tokens=*" %%i in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike '169.254*' -and $_.IPv4Address -notlike '127.*' } | Select-Object -First 1).IPAddress"') do set LAN_IP=%%i

if not defined LAN_IP set LAN_IP=127.0.0.1

if %errorLevel% equ 0 (
    echo.
    echo ======================================================================
    echo [SUCCES] Le port 8000 est desormais ouvert sur tous les profils reseau !
    echo Vous pouvez acceder a l'application sur votre iPhone / iPad / Laptop :
    echo    Lien Wi-Fi : http://%LAN_IP%:8000
    echo ======================================================================
    echo.
) else (
    echo.
    echo [AVERTISSEMENT] Verifiez que votre compte dispose des droits Administrateur.
)

echo Appuyez sur une touche pour continuer...
pause >nul
