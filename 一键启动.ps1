# 停止占用9002端口的进程
Write-Host "正在停止占用9002端口的进程..."
$processes = netstat -ano | Select-String ":9002"
foreach ($process in $processes) {
    $processId = $process.Line.Split()[-1]
    Write-Host "停止进程 $processId..."
    try {
        Stop-Process -Id $processId -Force
    } catch {
        Write-Host "停止进程 $processId 失败: $_"
    }
}

# 启动服务
Write-Host "正在启动内网运维助手服务..."
Write-Host "============================"
Write-Host "服务地址：http://localhost:9002"
Write-Host "前端界面：http://localhost:9002/static/index.html"
Write-Host "============================"
Write-Host "按 Ctrl+C 停止服务"

python -m uvicorn app:app --host 0.0.0.0 --port 9002
