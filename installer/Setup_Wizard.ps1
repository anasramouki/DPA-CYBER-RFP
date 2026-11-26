Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

# Setup Form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Assistant d'Installation — CyberRFP Maroc v2.0 (DPA)"
$form.Size = New-Object System.Drawing.Size(560, 430)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(248, 250, 252)

# Global Variables
$script:currentPage = 1
$script:installPath = [System.IO.Path]::Combine($env:LOCALAPPDATA, "DataProtech", "CyberRFP Maroc")
$projectRoot = Split-Path -Parent $PSScriptRoot

# Top Banner Header
$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Size = New-Object System.Drawing.Size(560, 75)
$headerPanel.Location = New-Object System.Drawing.Point(0, 0)
$headerPanel.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$form.Controls.Add($headerPanel)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "CYBERRFP MAROC — INSTALLATEUR DPA"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(249, 115, 22)
$titleLabel.Location = New-Object System.Drawing.Point(20, 14)
$titleLabel.AutoSize = $true
$headerPanel.Controls.Add($titleLabel)

$subLabel = New-Object System.Windows.Forms.Label
$subLabel.Text = "DataProtech Group (@dpg-cyber.com) · Veille Marchés Publics en Temps Réel"
$subLabel.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$subLabel.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$subLabel.Location = New-Object System.Drawing.Point(21, 40)
$subLabel.AutoSize = $true
$headerPanel.Controls.Add($subLabel)

# Bottom Navigation Panel
$footerPanel = New-Object System.Windows.Forms.Panel
$footerPanel.Size = New-Object System.Drawing.Size(560, 60)
$footerPanel.Location = New-Object System.Drawing.Point(0, 335)
$footerPanel.BackColor = [System.Drawing.Color]::FromArgb(241, 245, 249)
$form.Controls.Add($footerPanel)

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Text = "Annuler"
$btnCancel.Size = New-Object System.Drawing.Size(85, 30)
$btnCancel.Location = New-Object System.Drawing.Point(440, 15)
$btnCancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$btnCancel.Add_Click({ $form.Close() })
$footerPanel.Controls.Add($btnCancel)

$btnNext = New-Object System.Windows.Forms.Button
$btnNext.Text = "Suivant >"
$btnNext.Size = New-Object System.Drawing.Size(95, 30)
$btnNext.Location = New-Object System.Drawing.Point(335, 15)
$btnNext.BackColor = [System.Drawing.Color]::FromArgb(249, 115, 22)
$btnNext.ForeColor = [System.Drawing.Color]::White
$btnNext.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$footerPanel.Controls.Add($btnNext)

$btnBack = New-Object System.Windows.Forms.Button
$btnBack.Text = "< Précédent"
$btnBack.Size = New-Object System.Drawing.Size(95, 30)
$btnBack.Location = New-Object System.Drawing.Point(235, 15)
$btnBack.Enabled = $false
$footerPanel.Controls.Add($btnBack)

# Container for Page Views
$bodyPanel = New-Object System.Windows.Forms.Panel
$bodyPanel.Size = New-Object System.Drawing.Size(520, 240)
$bodyPanel.Location = New-Object System.Drawing.Point(20, 85)
$form.Controls.Add($bodyPanel)

# ==================== PAGE 1: BIENVENUE ====================
$p1 = New-Object System.Windows.Forms.Panel
$p1.Size = New-Object System.Drawing.Size(520, 240)
$bodyPanel.Controls.Add($p1)

$p1Title = New-Object System.Windows.Forms.Label
$p1Title.Text = "Bienvenue dans l'assistant d'installation de CyberRFP Maroc"
$p1Title.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$p1Title.ForeColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$p1Title.Location = New-Object System.Drawing.Point(10, 10)
$p1Title.AutoSize = $true
$p1.Controls.Add($p1Title)

$p1Desc = New-Object System.Windows.Forms.Label
$p1Desc.Text = "Cet assistant installera la plateforme CyberRFP Maroc sur votre poste de travail.`n`n" +
  "Fonctionnalités incluses :`n" +
  "• Veille continue et alertes automatiques en temps réel (PMMP, TGR, Banques)`n" +
  "• Authentification d'équipe sécurisée pour le domaine @dpg-cyber.com`n" +
  "• Matrice complète de soumission DPA & Profils d'experts (Décret n° 2-22-431)`n" +
  "• Téléchargement direct des dossiers DCE en un clic sans login portail.`n`n" +
  "Cliquez sur 'Suivant' pour continuer."
$p1Desc.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$p1Desc.ForeColor = [System.Drawing.Color]::FromArgb(71, 85, 105)
$p1Desc.Location = New-Object System.Drawing.Point(12, 45)
$p1Desc.Size = New-Object System.Drawing.Size(495, 180)
$p1.Controls.Add($p1Desc)

# ==================== PAGE 2: DOSSIER D'INSTALLATION ====================
$p2 = New-Object System.Windows.Forms.Panel
$p2.Size = New-Object System.Drawing.Size(520, 240)
$p2.Visible = $false
$bodyPanel.Controls.Add($p2)

$p2Title = New-Object System.Windows.Forms.Label
$p2Title.Text = "Sélectionnez le dossier d'installation"
$p2Title.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$p2Title.Location = New-Object System.Drawing.Point(10, 10)
$p2Title.AutoSize = $true
$p2.Controls.Add($p2Title)

$p2Desc = New-Object System.Windows.Forms.Label
$p2Desc.Text = "L'application sera installée dans le dossier suivant :"
$p2Desc.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$p2Desc.Location = New-Object System.Drawing.Point(12, 45)
$p2Desc.AutoSize = $true
$p2.Controls.Add($p2Desc)

$txtPath = New-Object System.Windows.Forms.TextBox
$txtPath.Text = $script:installPath
$txtPath.Location = New-Object System.Drawing.Point(15, 75)
$txtPath.Size = New-Object System.Drawing.Size(390, 25)
$p2.Controls.Add($txtPath)

$btnBrowse = New-Object System.Windows.Forms.Button
$btnBrowse.Text = "Parcourir..."
$btnBrowse.Location = New-Object System.Drawing.Point(415, 74)
$btnBrowse.Size = New-Object System.Drawing.Size(90, 26)
$btnBrowse.Add_Click({
    $fbd = New-Object System.Windows.Forms.FolderBrowserDialog
    $fbd.SelectedPath = $txtPath.Text
    if ($fbd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $txtPath.Text = $fbd.SelectedPath
        $script:installPath = $fbd.SelectedPath
    }
})
$p2.Controls.Add($btnBrowse)

# ==================== PAGE 3: OPTIONS ====================
$p3 = New-Object System.Windows.Forms.Panel
$p3.Size = New-Object System.Drawing.Size(520, 240)
$p3.Visible = $false
$bodyPanel.Controls.Add($p3)

$p3Title = New-Object System.Windows.Forms.Label
$p3Title.Text = "Options supplémentaires d'intégration"
$p3Title.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$p3Title.Location = New-Object System.Drawing.Point(10, 10)
$p3Title.AutoSize = $true
$p3.Controls.Add($p3Title)

$chkDesktop = New-Object System.Windows.Forms.CheckBox
$chkDesktop.Text = "Créer une icône de raccourci sur le Bureau"
$chkDesktop.Checked = $true
$chkDesktop.Location = New-Object System.Drawing.Point(15, 50)
$chkDesktop.Size = New-Object System.Drawing.Size(400, 25)
$p3.Controls.Add($chkDesktop)

$chkStartMenu = New-Object System.Windows.Forms.CheckBox
$chkStartMenu.Text = "Ajouter un raccourci dans le Menu Démarrer"
$chkStartMenu.Checked = $true
$chkStartMenu.Location = New-Object System.Drawing.Point(15, 85)
$chkStartMenu.Size = New-Object System.Drawing.Size(400, 25)
$p3.Controls.Add($chkStartMenu)

$chkAutoStart = New-Object System.Windows.Forms.CheckBox
$chkAutoStart.Text = "Démarrer automatiquement en tâche de fond pour la veille temps réel"
$chkAutoStart.Checked = $true
$chkAutoStart.Location = New-Object System.Drawing.Point(15, 120)
$chkAutoStart.Size = New-Object System.Drawing.Size(490, 25)
$p3.Controls.Add($chkAutoStart)

# ==================== PAGE 4: INSTALLATION EN COURS ====================
$p4 = New-Object System.Windows.Forms.Panel
$p4.Size = New-Object System.Drawing.Size(520, 240)
$p4.Visible = $false
$bodyPanel.Controls.Add($p4)

$p4Title = New-Object System.Windows.Forms.Label
$p4Title.Text = "Installation en cours..."
$p4Title.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$p4Title.Location = New-Object System.Drawing.Point(10, 10)
$p4Title.AutoSize = $true
$p4.Controls.Add($p4Title)

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "Préparation des fichiers..."
$lblStatus.Location = New-Object System.Drawing.Point(15, 45)
$lblStatus.Size = New-Object System.Drawing.Size(480, 20)
$p4.Controls.Add($lblStatus)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(15, 75)
$progressBar.Size = New-Object System.Drawing.Size(490, 25)
$p4.Controls.Add($progressBar)

# ==================== PAGE 5: FIN ====================
$p5 = New-Object System.Windows.Forms.Panel
$p5.Size = New-Object System.Drawing.Size(520, 240)
$p5.Visible = $false
$bodyPanel.Controls.Add($p5)

$p5Title = New-Object System.Windows.Forms.Label
$p5Title.Text = "Installation de CyberRFP Maroc terminée !"
$p5Title.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$p5Title.ForeColor = [System.Drawing.Color]::FromArgb(5, 150, 105)
$p5Title.Location = New-Object System.Drawing.Point(10, 10)
$p5Title.AutoSize = $true
$p5.Controls.Add($p5Title)

$p5Desc = New-Object System.Windows.Forms.Label
$p5Desc.Text = "CyberRFP Maroc a été installé avec succès sur votre ordinateur.`n`n" +
  "Votre équipe DataProtech peut se connecter immédiatement avec leurs identifiants @dpg-cyber.com.`n" +
  "La surveillance et le téléchargement des DCE s'effectuent en temps réel."
$p5Desc.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$p5Desc.Location = New-Object System.Drawing.Point(12, 45)
$p5Desc.Size = New-Object System.Drawing.Size(490, 80)
$p5.Controls.Add($p5Desc)

$chkLaunchNow = New-Object System.Windows.Forms.CheckBox
$chkLaunchNow.Text = "Lancer CyberRFP Maroc maintenant"
$chkLaunchNow.Checked = $true
$chkLaunchNow.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
$chkLaunchNow.Location = New-Object System.Drawing.Point(15, 135)
$chkLaunchNow.Size = New-Object System.Drawing.Size(400, 25)
$p5.Controls.Add($chkLaunchNow)

# Navigation Handler
$btnNext.Add_Click({
    if ($script:currentPage -eq 1) {
        $p1.Visible = $false
        $p2.Visible = $true
        $btnBack.Enabled = $true
        $script:currentPage = 2
    } elseif ($script:currentPage -eq 2) {
        $script:installPath = $txtPath.Text
        $p2.Visible = $false
        $p3.Visible = $true
        $btnNext.Text = "Installer"
        $script:currentPage = 3
    } elseif ($script:currentPage -eq 3) {
        $p3.Visible = $false
        $p4.Visible = $true
        $btnBack.Enabled = $false
        $btnNext.Enabled = $false
        $btnCancel.Enabled = $false
        $script:currentPage = 4
        
        # Run Installation Task
        $form.Refresh()
        $dest = $script:installPath
        
        $lblStatus.Text = "Création du répertoire $dest..."
        $progressBar.Value = 20
        $form.Refresh()
        if (-not (Test-Path $dest)) {
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
        }
        
        $lblStatus.Text = "Copie de l'exécutable et de la base de données..."
        $progressBar.Value = 50
        $form.Refresh()
        
        $srcExe = Join-Path $projectRoot "CyberRFP-Maroc.exe"
        if (-not (Test-Path $srcExe)) {
            $srcExe = Join-Path $projectRoot "dist\CyberRFP-Maroc.exe"
        }
        $srcDb = Join-Path $projectRoot "cyberrfp.db"
        if (-not (Test-Path $srcDb)) {
            $srcDb = Join-Path $projectRoot "dist\cyberrfp.db"
        }
        $srcLogo = Join-Path $projectRoot "src\static\dpa_logo.png"
        
        if (Test-Path $srcExe) {
            Copy-Item $srcExe -Destination (Join-Path $dest "CyberRFP-Maroc.exe") -Force
        }
        if (Test-Path $srcDb) {
            $destDb = Join-Path $dest "cyberrfp.db"
            Copy-Item $srcDb -Destination $destDb -Force
        }
        $destStatic = Join-Path $dest "static"
        if (-not (Test-Path $destStatic)) { New-Item -ItemType Directory -Path $destStatic -Force | Out-Null }
        if (Test-Path $srcLogo) {
            Copy-Item $srcLogo -Destination $destStatic -Force
        }

        # Create Shortcuts
        $lblStatus.Text = "Création des raccourcis..."
        $progressBar.Value = 80
        $form.Refresh()
        
        $installedExe = Join-Path $dest "CyberRFP-Maroc.exe"
        $wsh = New-Object -ComObject WScript.Shell
        
        if ($chkDesktop.Checked) {
            $desktopLink = $wsh.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath("Desktop"), "CyberRFP Maroc.lnk"))
            $desktopLink.TargetPath = $installedExe
            $desktopLink.WorkingDirectory = $dest
            $desktopLink.Description = "CyberRFP Maroc - DataProtech Group"
            $desktopLink.Save()
        }
        
        if ($chkStartMenu.Checked) {
            $smDir = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("StartMenu"), "Programs", "DataProtech")
            if (-not (Test-Path $smDir)) { New-Item -ItemType Directory -Path $smDir -Force | Out-Null }
            $smLink = $wsh.CreateShortcut([System.IO.Path]::Combine($smDir, "CyberRFP Maroc.lnk"))
            $smLink.TargetPath = $installedExe
            $smLink.WorkingDirectory = $dest
            $smLink.Description = "CyberRFP Maroc - DataProtech Group"
            $smLink.Save()
        }
        
        if ($chkAutoStart.Checked) {
            $startupDir = [System.Environment]::GetFolderPath("Startup")
            $startLink = $wsh.CreateShortcut([System.IO.Path]::Combine($startupDir, "CyberRFP Maroc AutoStart.lnk"))
            $startLink.TargetPath = $installedExe
            $startLink.WorkingDirectory = $dest
            $startLink.Description = "CyberRFP Maroc Background Monitoring"
            $startLink.Save()
        }

        $progressBar.Value = 100
        $lblStatus.Text = "Installation terminée !"
        $form.Refresh()
        Start-Sleep -Milliseconds 600
        
        $p4.Visible = $false
        $p5.Visible = $true
        $btnNext.Text = "Terminer"
        $btnNext.Enabled = $true
        $script:currentPage = 5
    } elseif ($script:currentPage -eq 5) {
        if ($chkLaunchNow.Checked) {
            $installedExe = Join-Path $script:installPath "CyberRFP-Maroc.exe"
            if (Test-Path $installedExe) {
                Start-Process -FilePath $installedExe -WorkingDirectory $script:installPath
            }
        }
        $form.Close()
    }
})

$btnBack.Add_Click({
    if ($script:currentPage -eq 2) {
        $p2.Visible = $false
        $p1.Visible = $true
        $btnBack.Enabled = $false
        $script:currentPage = 1
    } elseif ($script:currentPage -eq 3) {
        $p3.Visible = $false
        $p2.Visible = $true
        $btnNext.Text = "Suivant >"
        $script:currentPage = 2
    }
})

[void]$form.ShowDialog()
