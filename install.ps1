param(
  [ValidateSet('all', 'claude', 'codex')][string]$Client = 'all',
  [switch]$SkillsOnly,
  [switch]$Apply,
  [switch]$Force,
  [switch]$FilesOnly,
  [string]$TargetHome
)
$ErrorActionPreference = 'Stop'
$setupArgs = @((Join-Path $PSScriptRoot 'setup.py'))
if ($Apply) { $setupArgs += '--apply' }
if ($Force) { $setupArgs += '--replace' }
if ($FilesOnly) { $setupArgs += '--files-only' }
if ($SkillsOnly -or $Client -ne 'all') { $setupArgs += @('--skills-only', '--client', $Client) }
if ($TargetHome) { $setupArgs += @('--home', $TargetHome) }
& python @setupArgs
exit $LASTEXITCODE
