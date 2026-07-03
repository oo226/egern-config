# 一键推送到 GitHub: https://github.com/oo226/egern-config
# 在 Cursor 终端运行: .\scripts\push-to-github.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

# 去掉 Gitee 凭据干扰 (若存在)
git config --global --unset credential.https://gitee.com.provider 2>$null

if (-not (git rev-parse HEAD 2>$null)) {
  git add .
  git commit -m "init: Egern config with rule sync workflow"
}

git branch -M main

$remote = git remote get-url origin 2>$null
$target = 'https://github.com/oo226/egern-config.git'
if ($remote -ne $target) {
  if ($remote) { git remote remove origin }
  git remote add origin $target
}

Write-Host ''
Write-Host '>>> 若提示 Repository not found, 请先在 GitHub 创建空仓库:'
Write-Host '    https://github.com/new  名称填 egern-config (Public, 不要勾选 README)'
Write-Host ''
Write-Host '正在推送到 GitHub... (若弹出窗口, 请选择 GitHub 登录)'
Write-Host '仓库地址: https://github.com/oo226/egern-config'
Write-Host ''
git push -u origin main
