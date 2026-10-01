param(
    [string]$Project = '',
    [string[]]$Tools = @(),
    [ValidateSet('minimal', 'balanced', 'full')][string]$Profile = 'balanced',
    [string]$Skills = '',
    [switch]$NoRules,
    [switch]$Link,
    [switch]$Uninstall,
    [switch]$DryRun,
    [switch]$Doctor,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
$TokenSaverArgs = @((Join-Path $PSScriptRoot 'install.py'), '--profile', $Profile)
if ($Project) { $TokenSaverArgs += @('--project', $Project) }
if ($Tools.Count -gt 0) { $TokenSaverArgs += @('--tools', ($Tools -join ',')) }
if ($Skills) { $TokenSaverArgs += @('--skills', $Skills) }
if ($NoRules) { $TokenSaverArgs += '--no-rules' }
if ($Link) { $TokenSaverArgs += '--link' }
if ($Uninstall) { $TokenSaverArgs += '--uninstall' }
if ($DryRun) { $TokenSaverArgs += '--dry-run' }
if ($Doctor) { $TokenSaverArgs += '--doctor' }
if ($Force) { $TokenSaverArgs += '--force' }
if (Get-Command python -ErrorAction SilentlyContinue) {
    & python @TokenSaverArgs
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 @TokenSaverArgs
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @TokenSaverArgs
} else {
    throw 'Token Saver requires Python 3.8+ for installation.'
}
exit $LASTEXITCODE
