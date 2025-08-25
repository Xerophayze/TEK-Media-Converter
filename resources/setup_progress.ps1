Add-Type -AssemblyName System.Windows.Forms, System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Image Converter - Setup'
$form.StartPosition = 'CenterScreen'
$form.Width = 420
$form.Height = 140
$form.TopMost = $true

# Try to set the window icon to match the app icon in this resources folder
$iconPath = Join-Path $PSScriptRoot 'tekutah_logo_icon_Square.ico'
if (Test-Path $iconPath) {
    try { $form.Icon = New-Object System.Drawing.Icon($iconPath) } catch {}
}

$label = New-Object System.Windows.Forms.Label
$label.AutoSize = $true
$label.Text = 'Preparing environment'
$label.Left = 12
$label.Top = 10

$pb = New-Object System.Windows.Forms.ProgressBar
$pb.Style = 'Blocks'
$pb.Left = 12
$pb.Top = 40
$pb.Width = 380
$pb.Height = 20

$form.Controls.Add($label)
$form.Controls.Add($pb)
$form.Show()

try { $total = [int]$env:IC_TOTAL_STEPS } catch { $total = 0 }
if ($total -le 0) { $total = 5 }
$pb.Minimum = 0
$pb.Maximum = $total
$pb.Value = 0

$statusFile = [System.IO.Path]::Combine($env:TEMP, 'ic_setup_status.txt')
$flagFile = [System.IO.Path]::Combine($env:TEMP, 'ic_setup_done.flag')

while (-not (Test-Path $flagFile)) {
    if (Test-Path $statusFile) {
        try { $t = Get-Content -LiteralPath $statusFile -Raw -ErrorAction SilentlyContinue } catch {}
        if ($t) {
            $idx = $t.IndexOf('|')
            if ($idx -ge 0) {
                $left = $t.Substring(0,$idx)
                $right = $t.Substring($idx+1)
                try { $v = [int]$left } catch { $v = 0 }
                if ($v -ge $pb.Minimum -and $v -le $pb.Maximum) { $pb.Value = $v }
                $label.Text = $right.Trim()
            } else {
                $label.Text = $t
            }
        }
    }
    [System.Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 100
}

$form.Close()
