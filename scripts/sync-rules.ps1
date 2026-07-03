# 本地手动同步规则 (需能访问 GitHub)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$rulesDir = Join-Path $root 'Rules'
$skkDir = Join-Path $rulesDir 'skk'
New-Item -ItemType Directory -Force -Path $skkDir | Out-Null

$files = @(
  'Reject','ChinaDomain','Lan','Direct',
  'WeChat','Bilibili','AppleCN','ChinaIP','ChinaASN',
  'AI','Telegram','Twitter','TikTok',
  'YouTube','Netflix','Disney','Spotify','Emby',
  'Google','Github','Microsoft','AppleServers',
  'Game','ProxyGFW','Proxy'
)
$base = 'https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules'
foreach ($name in $files) {
  $uri = "$base/$name.yaml"
  $out = Join-Path $rulesDir "$name.yaml"
  Invoke-WebRequest -Uri $uri -OutFile $out -UseBasicParsing
  Write-Host "OK $name.yaml"
}
Invoke-WebRequest -Uri 'https://ruleset.skk.moe/List/domainset/reject.conf' -OutFile (Join-Path $skkDir 'reject.conf') -UseBasicParsing
Write-Host 'Done. Review with: git status'
