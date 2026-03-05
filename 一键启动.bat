@echo off

echo 正在停止占用9002端口的进程...
netstat -ano | findstr :9002 > ports.txt
if exist ports.txt (
    for /f "tokens=5" %%a in (ports.txt) do (
        echo 停止进程 %%a...
        taskkill /F /PID %%a
    )
    del ports.txt
)

echo 正在启动内网运维助手服务...
echo ================================
echo 服务地址：http://localhost:9002
echo 前端界面：http://localhost:9002/static/index.html
echo ================================
echo 按 Ctrl+C 停止服务

python -m uvicorn app:app --host 0.0.0.0 --port 9002
