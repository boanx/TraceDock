param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& $Python -m PyInstaller --noconfirm --onefile --windowed --name TraceDock `
    --icon (Join-Path $projectRoot "tracedock.ico") `
    --add-data "$(Join-Path $projectRoot 'tracedock.ico');." `
    --add-data "$(Join-Path $projectRoot 'tracedock.png');." `
    --version-file (Join-Path $projectRoot "version-info.txt") `
    --paths $projectRoot --collect-all nptdms --collect-all matplotlib `
    --exclude-module matplotlib.tests --exclude-module pandas `
    --distpath (Join-Path $projectRoot "dist") `
    --workpath (Join-Path $projectRoot "build") `
    --specpath (Join-Path $projectRoot "build") `
    (Join-Path $projectRoot "TraceDock.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
