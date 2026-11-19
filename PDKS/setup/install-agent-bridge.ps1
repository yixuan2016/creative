param([string]$Confirm = '')
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
if ($Confirm -ne 'INSTALL PDKS AGENT BRIDGE') {
    Write-Output 'PDKS Agent Bridge installation plan:'
    Write-Output '- Install npm dependencies locally under agent-native/ (official MCP Server, MCP Apps, Zod, Vite build toolchain).'
    Write-Output '- Network: npm registry only for package installation.'
    Write-Output '- Build the MCP Apps setup panel into agent-native/dist/.'
    Write-Output '- Do not modify Agent configuration files, install DWS, start collection or register background services.'
    Write-Output '- No administrator privileges are requested.'
    Write-Output 'To proceed after explicit user approval, rerun:'
    Write-Output '.\setup\install-agent-bridge.ps1 -Confirm "INSTALL PDKS AGENT BRIDGE"'
    exit 3
}
$Node = Get-Command node -ErrorAction SilentlyContinue
$Npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $Node -or -not $Npm) {
    throw 'PDKS Agent Bridge requires Node.js 22.12+ and npm. No system changes were made.'
}
$Version = [version](& node -p 'process.versions.node')
if ($Version -lt [version]'22.12.0') {
    throw "Node.js 22.12+ is required; found $Version. No system changes were made."
}
Push-Location (Join-Path $Root 'agent-native')
try {
    & npm install
    if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw 'MCP App UI build failed.' }
    & node .\bin\pdks-agent.js config --host generic
    if ($LASTEXITCODE -ne 0) { throw 'Could not generate MCP configuration preview.' }
}
finally { Pop-Location }
