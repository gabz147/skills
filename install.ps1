param(
  [ValidateSet('all', 'claude', 'codex')][string]$Client = 'all',
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$targets = @{
  claude = Join-Path $HOME '.claude\skills'
  codex  = Join-Path $HOME '.codex\skills'
}
foreach ($c in $targets.Keys) {
  if ($Client -ne 'all' -and $Client -ne $c) { continue }
  $src = Join-Path $repo $c
  $dst = $targets[$c]
  if (-not (Test-Path $src)) { Write-Warning "missing source folder $src"; continue }
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  $copied = 0; $skipped = 0
  foreach ($item in Get-ChildItem -Path $src) {
    $out = Join-Path $dst $item.Name
    if ((Test-Path $out) -and -not $Force) { $skipped++; continue }
    if ($item.PSIsContainer) {
      if (Test-Path $out) { Remove-Item -Recurse -Force $out }
      Copy-Item -Recurse -Force $item.FullName $out
    } else {
      Copy-Item -Force $item.FullName $out
    }
    $copied++
  }
  Write-Host ("{0}: copied {1}, skipped {2} existing -> {3}" -f $c, $copied, $skipped, $dst)
}
Write-Host 'Restart Claude Code / Codex so the skill lists reload.'
