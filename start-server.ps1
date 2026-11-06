# LoongBBS Next 本地启动脚本（Waitress）
# 用法： .\start-server.ps1
$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) {
    throw "找不到虚拟环境：$py`n请先执行 C:\Python314\python.exe -m venv .venv 并安装 requirements.txt"
}

$pidFile = Join-Path $repo '.server.pid'
if (Test-Path -LiteralPath $pidFile) {
    $oldPid = (Get-Content -LiteralPath $pidFile -Raw).Trim()
    if ($oldPid -match '^\d+$') {
        $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
        if ($proc) {
            throw "服务已经在运行（PID $oldPid）。请先执行 .\stop-server.ps1"
        }
    }
}

# 读取 .env.local 里的环境变量（SECRET_KEY 等）
$envFile = Join-Path $repo '.env.local'
if (Test-Path -LiteralPath $envFile) {
    Get-Content -LiteralPath $envFile -Encoding utf8 | ForEach-Object {
        if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.+)$') {
            Set-Item -Path "env:$($matches[1])" -Value $matches[2]
        }
    }
}

$logDir = Join-Path $repo 'logs'
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$proc = Start-Process -FilePath $py `
    -ArgumentList (Join-Path $repo 'serve.py') `
    -WorkingDirectory $repo `
    -WindowStyle Hidden `
    -PassThru `
    -RedirectStandardOutput (Join-Path $logDir 'server.out.log') `
    -RedirectStandardError (Join-Path $logDir 'server.err.log')

Start-Sleep -Seconds 2
if ($proc.HasExited) {
    throw "启动失败，退出码 $($proc.ExitCode)。请看 logs\server.err.log"
}

Set-Content -LiteralPath $pidFile -Value $proc.Id -Encoding utf8
$port = if ($env:LOONG_BBS_PORT) { $env:LOONG_BBS_PORT } else { '5000' }
Write-Host "LoongBBS Next 已启动：http://127.0.0.1:$port  (PID $($proc.Id))"
Write-Host "日志：logs\server.out.log / logs\server.err.log"
