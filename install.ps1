<#
.SYNOPSIS
  Token Saver Skills installer for Windows: Claude Code, Codex, opencode, ZCode,
  Gemini CLI, Cursor and GitHub Copilot. Works on Windows PowerShell 5.1 and PowerShell 7+.

.EXAMPLE
  .\install.ps1                          # global install for every tool found
  .\install.ps1 -Project C:\code\my-app  # install into one project
  .\install.ps1 -Tools claude,codex      # only these tools
  .\install.ps1 -Uninstall               # remove skills + rules block

  If scripts are blocked:  powershell -ExecutionPolicy Bypass -File .\install.ps1
#>
[CmdletBinding()]
param(
  [string]$Project = "",
  [string[]]$Tools = @(),
  [switch]$NoRules,
  [switch]$Uninstall,
  [switch]$DryRun
)
$ErrorActionPreference = 'Stop'

$RepoDir   = $PSScriptRoot
$SkillsSrc = Join-Path $RepoDir 'skills'
$BlockSrc  = Join-Path (Join-Path $RepoDir 'rules') 'token-saver-block.md'
$Skills    = @('token-saver', 'repo-map', 'smart-read', 'quiet-run', 'session-memory')
$AllTools  = @('claude', 'codex', 'opencode', 'zcode', 'gemini', 'cursor', 'copilot')
$Start     = '<!-- token-saver:start'
$End       = '<!-- token-saver:end -->'
$HomeDir   = [Environment]::GetFolderPath('UserProfile')
$CodexDir  = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HomeDir '.codex' }
$ConfigDir = if ($env:XDG_CONFIG_HOME) { $env:XDG_CONFIG_HOME } else { Join-Path $HomeDir '.config' }

function Has([string]$cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Say([string]$msg) { Write-Host $msg }
function Fwd([string]$p) { $p -replace '\\', '/' }   # forward slashes work in PowerShell, cmd and Git Bash
function Write-Utf8([string]$path, [string]$text) {
  [IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
}

# ---------------------------------------------------------------- tools
$Tools = @($Tools | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ })
if ($Tools -contains 'all') { $Tools = $AllTools }
$Rules = -not $NoRules
if ($Tools.Count -eq 0) {
  if ($Project) { $Tools = $AllTools }
  else {
    $found = @()
    if ((Test-Path (Join-Path $HomeDir '.claude')) -or (Has 'claude')) { $found += 'claude' }
    if ((Test-Path $CodexDir) -or (Has 'codex')) { $found += 'codex' }
    if ((Test-Path (Join-Path $ConfigDir 'opencode')) -or (Has 'opencode')) { $found += 'opencode' }
    if ((Test-Path (Join-Path $HomeDir '.zcode')) -or (Has 'zcode')) { $found += 'zcode' }
    if ((Test-Path (Join-Path $HomeDir '.gemini')) -or (Has 'gemini')) { $found += 'gemini' }
    if ((Test-Path (Join-Path $HomeDir '.cursor')) -or (Has 'cursor')) { $found += 'cursor' }
    if ((Test-Path (Join-Path $HomeDir '.copilot')) -or (Has 'copilot')) { $found += 'copilot' }
    if ($found.Count -eq 0) {
      Say 'No AI coding tool detected; installing skills to ~/.claude/skills and ~/.agents/skills only.'
      Say 'Re-run with -Tools claude,codex,... to also add the always-on rules block.'
      $found = @('claude', 'codex'); $Rules = $false
    }
    $Tools = $found
  }
}
foreach ($t in $Tools) {
  if ($AllTools -notcontains $t) { throw "unknown tool: $t (valid: $($AllTools -join ','))" }
}

$Py = 'python'
if (-not (Has 'python') -and (Has 'py')) { $Py = 'py -3' }
if (-not (Has 'python') -and -not (Has 'py') -and (Has 'python3')) { $Py = 'python3' }

if ($Project) {
  if (-not (Test-Path $Project -PathType Container)) { throw "not a directory: $Project" }
  $Base = (Resolve-Path $Project).Path
  $ClaudeSkills = Join-Path (Join-Path $Base '.claude') 'skills'; $ClaudeRef = '.claude/skills'
  $AgentsSkills = Join-Path (Join-Path $Base '.agents') 'skills'; $AgentsRef = '.agents/skills'
} else {
  $Base = $HomeDir
  $ClaudeSkills = Join-Path (Join-Path $HomeDir '.claude') 'skills'; $ClaudeRef = Fwd $ClaudeSkills
  $AgentsSkills = Join-Path (Join-Path $HomeDir '.agents') 'skills'; $AgentsRef = Fwd $AgentsSkills
}

# ---------------------------------------------------------------- plan
$SkillDests = New-Object System.Collections.ArrayList
$RuleTargets = [ordered]@{}   # file -> skills ref
$Notes = @()
foreach ($t in $Tools) {
  $d = if ($t -eq 'claude') { $ClaudeSkills } else { $AgentsSkills }
  if (-not $SkillDests.Contains($d)) { [void]$SkillDests.Add($d) }
  if ($Project) {
    switch ($t) {
      'claude' { $f = Join-Path $Base 'CLAUDE.md'; $r = $ClaudeRef }
      'gemini' { $f = Join-Path $Base 'GEMINI.md'; $r = $AgentsRef }
      default  { $f = Join-Path $Base 'AGENTS.md'; $r = $AgentsRef }
    }
  } else {
    $r = $AgentsRef
    switch ($t) {
      'claude'   { $f = Join-Path (Join-Path $HomeDir '.claude') 'CLAUDE.md'; $r = $ClaudeRef }
      'codex'    { $f = Join-Path $CodexDir 'AGENTS.md' }
      'opencode' { $f = Join-Path (Join-Path $ConfigDir 'opencode') 'AGENTS.md' }
      'zcode'    { $f = Join-Path (Join-Path $HomeDir '.zcode') 'AGENTS.md' }
      'gemini'   { $f = Join-Path (Join-Path $HomeDir '.gemini') 'GEMINI.md' }
      'copilot'  { $f = Join-Path (Join-Path $HomeDir '.copilot') 'copilot-instructions.md' }
      'cursor'   {
        $f = $null
        $Notes += 'Cursor has no global rules file: paste rules/token-saver-block.md into Cursor Settings > Rules > User Rules, or use -Project DIR (writes AGENTS.md).'
      }
    }
  }
  if ($f -and -not $RuleTargets.Contains($f)) { $RuleTargets[$f] = $r }
}

# ---------------------------------------------------------------- actions
function Install-Skills([string]$dest) {
  if ($DryRun) { Say "  [dry-run] copy skills -> $dest"; return }
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  foreach ($s in $Skills) {
    $target = Join-Path $dest $s
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    Copy-Item -Recurse -Force (Join-Path $SkillsSrc $s) $target
  }
  Say "  skills -> $dest ($($Skills -join ' '))"
}

function Remove-Skills([string]$dest) {
  foreach ($s in $Skills) {
    $target = Join-Path $dest $s
    if (Test-Path $target) {
      if ($DryRun) { Say "  [dry-run] remove $target" } else { Remove-Item -Recurse -Force $target; Say "  removed $target" }
    }
  }
  foreach ($d in @($dest, (Split-Path -Parent $dest))) {
    if (-not $DryRun -and (Test-Path $d) -and -not (Get-ChildItem -Force $d | Select-Object -First 1)) { Remove-Item -Force $d }
  }
}

function Set-Rules([string]$file, [string]$ref) {
  if ($DryRun) { Say "  [dry-run] rules block -> $file"; return }
  $block = ([IO.File]::ReadAllText($BlockSrc)).Replace('{{SKILLS_DIR}}', $ref).Replace('{{PY}}', $Py).TrimEnd()
  $dir = Split-Path -Parent $file
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  if (Test-Path $file) {
    $text = [IO.File]::ReadAllText($file)
    $s = $text.IndexOf($Start); $e = $text.IndexOf($End)
    if ($s -ge 0 -and $e -gt $s) {
      Write-Utf8 $file ($text.Substring(0, $s) + $block + $text.Substring($e + $End.Length))
      Say "  updated rules block: $file"
    } elseif ($s -ge 0) {
      Say "  SKIPPED ${file}: start marker without end marker; fix it by hand"
    } elseif ($text.Trim().Length -gt 0) {
      Write-Utf8 $file ($text.TrimEnd() + "`n`n" + $block + "`n")
      Say "  appended rules block: $file"
    } else {
      Write-Utf8 $file ($block + "`n"); Say "  created: $file"
    }
  } else {
    Write-Utf8 $file ($block + "`n"); Say "  created: $file"
  }
}

function Remove-Rules([string]$file) {
  if (-not (Test-Path $file)) { return }
  $text = [IO.File]::ReadAllText($file)
  $s = $text.IndexOf($Start); $e = $text.IndexOf($End)
  if ($s -lt 0 -or $e -le $s) { return }
  if ($DryRun) { Say "  [dry-run] remove rules block from $file"; return }
  $rest = ($text.Substring(0, $s).TrimEnd() + $text.Substring($e + $End.Length)).Trim()
  if ($rest.Length -eq 0) { Remove-Item -Force $file; Say "  removed empty: $file" }
  else { Write-Utf8 $file ($rest + "`n"); Say "  removed rules block: $file" }
}

# ---------------------------------------------------------------- go
$modeName = if ($Project) { 'project' } else { 'global' }
$action = if ($Uninstall) { 'uninstall' } else { 'install' }
Say "Token Saver Skills: $action ($modeName; tools: $($Tools -join ' '))"

if ($Uninstall) {
  foreach ($d in $SkillDests) { Remove-Skills $d }
  foreach ($f in @($RuleTargets.Keys)) { Remove-Rules $f }
  Say 'Done. (.codemap/ folders inside your projects are left alone.)'
  exit 0
}

foreach ($d in $SkillDests) { Install-Skills $d }
if ($Rules) { foreach ($f in @($RuleTargets.Keys)) { Set-Rules $f $RuleTargets[$f] } }
foreach ($n in $Notes) { Say "  note: $n" }
if (-not (Has 'python') -and -not (Has 'py') -and -not (Has 'python3')) {
  Say '  note: Python 3 not found. The skills still work (rg/grep fallbacks), but repomap/quiet_run need Python 3.8+ (winget install Python.Python.3.12).'
}
Say 'Done. Restart your coding tool so it picks up the new skills.'
