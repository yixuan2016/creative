$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 --version *> $null
  if ($LASTEXITCODE -eq 0) { $Python = 'py'; $PythonArgs = @('-3') }
}
if (-not $Python -and (Get-Command python -ErrorAction SilentlyContinue)) {
  & python --version *> $null
  if ($LASTEXITCODE -eq 0) { $Python = 'python'; $PythonArgs = @() }
}
if (-not $Python) {
  Write-Error 'PDKS Setup requires Python 3.10+. No Python installation was changed. Ask your Agent to install Python 3.12 for the current user, then rerun.'
  exit 2
}
$Engine = Join-Path $Root 'skills/pdks-setup/scripts/pdks_setup.py'
& $Python @PythonArgs $Engine --bundle-root $Root @args
exit $LASTEXITCODE
