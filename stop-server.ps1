# LoongBBS Next 停止脚本
# 用法： .\stop-server.ps1
$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $repo '.server.pid'

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "没有找到 .server.pid，服务可能未通过 start-server.ps1 启动。"
    exit 0
}

$serverPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
if ($serverPid -notmatch '^\d+$') {
    throw ".server.pid 内容不合法：$serverPid"
}

$proc = Get-Process -Id ([int]$serverPid) -ErrorAction SilentlyContinue
if ($proc) {
    Stop-Process -Id ([int]$serverPid) -Force
    Write-Host "已停止 LoongBBS Next（PID $serverPid）"
} else {
    Write-Host "PID $serverPid 已经不在运行"
}

Remove-Item -LiteralPath $pidFile -Force
