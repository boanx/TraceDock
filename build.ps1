param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$splashPath = Join-Path $projectRoot 'build/startup.png'
& $Python (Join-Path $projectRoot 'make_splash.py') $splashPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$tlsPolicyPath = & $Python -c "import pathlib,ssl; print(pathlib.Path(ssl.__file__).with_name('codex-rejected-cas.pem'))"
$tlsData = @()
if (Test-Path -LiteralPath $tlsPolicyPath) {
    $tlsData = @('--add-data', ($tlsPolicyPath + ';.'))
}
& $Python -m PyInstaller @tlsData --noconfirm --onefile --windowed --name TraceDock `
    --icon (Join-Path $projectRoot "tracedock.ico") `
    --manifest (Join-Path $projectRoot "TraceDock.manifest") `
    --add-data "$(Join-Path $projectRoot 'tracedock.ico');." `
    --add-data "$(Join-Path $projectRoot 'tracedock.png');." `
    --version-file (Join-Path $projectRoot "version-info.txt") `
    --paths $projectRoot --splash $splashPath `
    --exclude-module matplotlib.tests --exclude-module pandas `
    --distpath (Join-Path $projectRoot "dist") `
    --workpath (Join-Path $projectRoot "build") `
    --specpath (Join-Path $projectRoot "build") `
    (Join-Path $projectRoot "TraceDock.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
