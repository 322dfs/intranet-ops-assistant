from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from ssh_client import run_ssh_command, test_server_connection
from ai_client import get_ai_response
from database import get_db, create_tables, init_default_server, Server, Command
from config import SERVER_GROUPS


app = FastAPI(title="内网运维助手工具后端 Intranet Ops Tools API")

# 配置静态文件目录
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9002"],  # 明确设置前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    print("正在初始化数据库...")
    try:
        create_tables()
        init_default_server()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")


def is_linux_command(text):
    """
    判断输入是否是Linux命令
    """
    # 常见Linux命令列表
    common_commands = [
        'ls', 'ps', 'top', 'df', 'free', 'ip', 'netstat', 'ss',
        'grep', 'awk', 'sed', 'cat', 'tail', 'head', 'wc',
        'find', 'locate', 'which', 'whereis', 'type',
        'chmod', 'chown', 'chgrp', 'umask',
        'tar', 'gzip', 'gunzip', 'zip', 'unzip',
        'ping', 'traceroute', 'nslookup', 'dig', 'curl', 'wget',
        'systemctl', 'service', 'journalctl',
        'uname', 'hostname', 'whoami', 'id', 'date', 'uptime',
        'du', 'fdisk', 'mount', 'umount',
        'kill', 'killall', 'pkill',
        'history', 'env', 'export', 'echo', 'printf',
        'sort', 'uniq', 'cut', 'tr', 'tee',
        'ln', 'mv', 'cp', 'rm', 'mkdir', 'rmdir', 'touch',
        'cd', 'pwd',
        'less', 'more', 'vim', 'vi', 'nano',
        'man', 'help',
        'docker', 'docker-compose', 'kubectl',
        'git', 'svn', 'hg',
        'npm', 'pip', 'yum', 'apt', 'apt-get',
        'python', 'python3', 'node', 'java', 'gcc', 'g++',
        'make', 'cmake', 'gcc', 'g++',
        'lsof', 'fuser', 'strace', 'ltrace',
        'tcpdump', 'wireshark',
        'ssh', 'scp', 'rsync', 'sftp',
        'crontab', 'at',
        'useradd', 'userdel', 'usermod', 'groupadd', 'groupdel',
        'passwd', 'su', 'sudo',
        'last', 'who', 'w',
        'dmesg', 'lsmod', 'modprobe', 'insmod', 'rmmod',
        'lsblk', 'blkid',
        'stat', 'file', 'md5sum', 'sha256sum'
    ]
    
    # 去除首尾空格
    text = text.strip()
    
    # 检查是否包含中文字符
    if any(ord(c) > 127 for c in text):
        return False
    
    # 检查是否以常见Linux命令开头
    for cmd in common_commands:
        if text.startswith(cmd) or text.startswith(f'{cmd} '):
            return True
    
    # 检查是否包含管道、重定向等命令特征
    if '|' in text or '>' in text or '<' in text or '>>' in text:
        return True
    
    # 检查是否是绝对路径命令
    if text.startswith('/') or text.startswith('./'):
        return True
    
    # 检查是否包含sudo
    if text.startswith('sudo '):
        return True
    
    return False


def is_command_safe(cmd):
    """
    检查命令是否安全
    """
    # 危险命令黑名单
    dangerous_patterns = [
        'rm -rf /',
        'rm -rf /*',
        'dd if=/dev/zero',
        'dd if=/dev/random',
        ':(){ :|:& };:',
        'mkfs',
        'format',
        'shutdown',
        'reboot',
        'poweroff',
        'halt',
        'init 0',
        'mv /dev/null',
        '> /dev/sda',
        'dd of=/dev/sda',
        'dd of=/dev/hda',
        'chmod 777 /',
        'chmod 777 /*',
        'chown root:root /',
        'chown root:root /*',
        'rm -f /bin',
        'rm -f /sbin',
        'rm -f /usr/bin',
        'rm -f /usr/sbin',
        'rm -f /etc/passwd',
        'rm -f /etc/shadow',
        'rm -f /boot',
        'rm -f /lib',
        'rm -f /lib64',
        'crontab -r',
        'crontab -e',
        'echo "" > /etc/passwd',
        'echo "" > /etc/shadow',
        'wget http://',
        'curl http://',
        'nc -l',
        'nc -e',
        'bash -i',
        'sh -i',
        'python -c',
        'perl -e',
        'ruby -e',
        'eval(',
        'exec(',
        'system(',
        'passthru(',
        'shell_exec(',
        'popen(',
        'proc_open(',
        '`', '$(',
        '$(',
        '${',
        '&& rm',
        '; rm',
        '| rm',
        '|| rm',
        '&& dd',
        '; dd',
        '| dd',
        '|| dd'
    ]
    
    # 转换为小写进行检查
    cmd_lower = cmd.lower()
    
    # 检查是否包含危险模式
    for pattern in dangerous_patterns:
        if pattern.lower() in cmd_lower:
            return False
    
    # 检查是否包含多个危险命令的组合
    if 'rm ' in cmd_lower and ('/' in cmd_lower or '*' in cmd_lower):
        # 如果是rm命令，检查是否包含根目录或通配符
        if '/ ' in cmd_lower or '/*' in cmd_lower or '/.' in cmd_lower:
            return False
    
    # 检查是否尝试修改系统关键文件
    critical_files = ['/etc/passwd', '/etc/shadow', '/etc/sudoers', '/etc/group', 
                     '/boot/', '/bin/', '/sbin/', '/lib/', '/lib64/', '/usr/bin/', '/usr/sbin/']
    for file in critical_files:
        if file in cmd and ('rm' in cmd_lower or 'mv' in cmd_lower or 'chmod' in cmd_lower or 'chown' in cmd_lower):
            return False
    
    return True


class CommandRequest(BaseModel):
    command: str
    server_id: int = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    server_id: int = None


class ServerBase(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    password: str
    group: str = "其他"
    description: str = None


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    name: str = None
    host: str = None
    port: int = None
    username: str = None
    password: str = None
    group: str = None
    description: str = None


from pydantic import ConfigDict


class ServerResponse(ServerBase):
    id: int
    status: str
    last_connected: datetime = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CommandResponse(BaseModel):
    id: int
    server_id: int
    command: str
    output: str = None
    exit_code: int = None
    executed_at: datetime
    executed_by: str
    
    model_config = ConfigDict(from_attributes=True)


@app.get("/health")
async def health():
    """
    健康检查接口：
    - 方便在 Coze 中配置 HTTP 工具前先测试服务是否可达。
    """
    return {"status": "ok", "service": "intranet-ops-tools"}


@app.get("/api/servers")
async def get_servers(db: Session = Depends(get_db)):
    """
    获取服务器列表
    """
    try:
        print("开始获取服务器列表...")
        servers = db.query(Server).all()
        print(f"获取到 {len(servers)} 个服务器")
        # 转换为字典列表
        server_list = []
        for server in servers:
            server_dict = {
                "id": server.id,
                "name": server.name,
                "host": server.host,
                "port": server.port,
                "username": server.username,
                "password": server.password,
                "group": server.group,
                "description": server.description,
                "status": server.status,
                "last_connected": server.last_connected,
                "created_at": server.created_at,
                "updated_at": server.updated_at
            }
            server_list.append(server_dict)
        print("服务器列表获取成功")
        return server_list
    except Exception as e:
        print(f"Error in get_servers: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.post("/api/servers", response_model=ServerResponse)
async def create_server(server: ServerCreate, db: Session = Depends(get_db)):
    """
    添加服务器
    """
    # 测试连接
    is_connected = test_server_connection(server.host, server.port, server.username, server.password)
    
    # 创建服务器
    db_server = Server(
        name=server.name,
        host=server.host,
        port=server.port,
        username=server.username,
        password=server.password,
        group=server.group,
        description=server.description,
        status="online" if is_connected else "offline",
        last_connected=datetime.utcnow() if is_connected else None
    )
    
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    return db_server


@app.put("/api/servers/{server_id}", response_model=ServerResponse)
async def update_server(server_id: int, server: ServerUpdate, db: Session = Depends(get_db)):
    """
    更新服务器信息
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    # 更新字段
    update_data = server.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_server, field, value)
    
    # 测试连接
    is_connected = test_server_connection(
        db_server.host, 
        db_server.port, 
        db_server.username, 
        db_server.password
    )
    
    db_server.status = "online" if is_connected else "offline"
    db_server.last_connected = datetime.utcnow() if is_connected else None
    db_server.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_server)
    
    return db_server


@app.delete("/api/servers/{server_id}")
async def delete_server(server_id: int, db: Session = Depends(get_db)):
    """
    删除服务器
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    db.delete(db_server)
    db.commit()
    
    return {"message": "服务器已删除"}


@app.get("/api/servers/{server_id}", response_model=ServerResponse)
async def get_server(server_id: int, db: Session = Depends(get_db)):
    """
    获取服务器详情
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    # 测试连接
    is_connected = test_server_connection(
        db_server.host, 
        db_server.port, 
        db_server.username, 
        db_server.password
    )
    
    db_server.status = "online" if is_connected else "offline"
    db_server.last_connected = datetime.utcnow() if is_connected else None
    db.commit()
    db.refresh(db_server)
    
    return db_server


@app.post("/api/servers/{server_id}/test")
async def test_server(server_id: int, db: Session = Depends(get_db)):
    """
    测试服务器连接
    """
    db_server = db.query(Server).filter(Server.id == server_id).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    
    is_connected = test_server_connection(
        db_server.host, 
        db_server.port, 
        db_server.username, 
        db_server.password
    )
    
    db_server.status = "online" if is_connected else "offline"
    db_server.last_connected = datetime.utcnow() if is_connected else None
    db.commit()
    
    return {"connected": is_connected, "status": db_server.status}


@app.get("/api/server-groups")
async def get_server_groups():
    """
    获取服务器分组
    """
    return {"groups": SERVER_GROUPS}


@app.post("/tools/ssh/run")
async def tools_ssh_run(req: CommandRequest, db: Session = Depends(get_db)):
    """
    通用 SSH 命令执行接口。
    建议在 Coze 中只对白名单命令使用此接口。
    """
    if not req.command.strip():
        raise HTTPException(status_code=400, detail="command 不能为空")

    # 获取服务器信息
    if req.server_id:
        db_server = db.query(Server).filter(Server.id == req.server_id).first()
        if not db_server:
            raise HTTPException(status_code=404, detail="服务器不存在")
        host = db_server.host
        port = db_server.port
        username = db_server.username
        password = db_server.password
    else:
        # 使用默认服务器
        db_server = db.query(Server).first()
        if not db_server:
            raise HTTPException(status_code=404, detail="没有可用的服务器")
        host = db_server.host
        port = db_server.port
        username = db_server.username
        password = db_server.password

    try:
        code, out, err = run_ssh_command(req.command, host, port, username, password)
        
        # 保存命令执行历史
        db_command = Command(
            server_id=db_server.id,
            command=req.command,
            output=out,
            exit_code=code,
            executed_by="system"
        )
        db.add(db_command)
        db.commit()
        
        # 更新服务器状态
        db_server.status = "online"
        db_server.last_connected = datetime.utcnow()
        db.commit()
    except Exception as e:
        # 更新服务器状态
        if db_server:
            db_server.status = "offline"
            db.commit()
        raise HTTPException(status_code=500, detail=f"连接或执行失败: {e}")

    return {
        "success": code == 0,
        "exit_code": code,
        "stdout": out,
        "stderr": err,
        "server_id": db_server.id,
        "server_name": db_server.name
    }


@app.get("/tools/metrics/cpu")
async def tools_metrics_cpu():
    """
    查看 CPU 情况：
    - 可在 Coze 中配置为"cpu_check"工具。
    """
    cmd = "top -b -n 1 | head -n 5"
    try:
        code, out, err = run_ssh_command(cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接或执行失败: {e}")

    return {
        "success": code == 0,
        "command": cmd,
        "exit_code": code,
        "stdout": out,
        "stderr": err,
    }


@app.get("/tools/metrics/memory")
async def tools_metrics_memory():
    """
    查看内存使用情况。
    """
    cmd = "free -h"
    try:
        code, out, err = run_ssh_command(cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接或执行失败: {e}")

    return {
        "success": code == 0,
        "command": cmd,
        "exit_code": code,
        "stdout": out,
        "stderr": err,
    }


@app.get("/tools/metrics/disk")
async def tools_metrics_disk():
    """
    查看磁盘使用情况。
    """
    cmd = "df -h"
    try:
        code, out, err = run_ssh_command(cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接或执行失败: {e}")

    return {
        "success": code == 0,
        "command": cmd,
        "exit_code": code,
        "stdout": out,
        "stderr": err,
    }


@app.get("/tools/metrics/load")
async def tools_metrics_load():
    """
    查看系统负载。
    """
    cmd = "uptime"
    try:
        code, out, err = run_ssh_command(cmd)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接或执行失败: {e}")

    return {
        "success": code == 0,
        "command": cmd,
        "exit_code": code,
        "stdout": out,
        "stderr": err,
    }


import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# 创建线程池执行器
executor = ThreadPoolExecutor(max_workers=4)

# 服务器数据缓存，避免频繁获取
server_data_cache = {}
cache_expiry = 60  # 缓存有效期，单位：秒


def get_server_data(host=None, port=None, username=None, password=None):
    """
    获取服务器性能数据，使用缓存避免频繁获取
    """
    current_time = time.time()
    
    # 生成缓存键
    cache_key = f"{host}:{port}:{username}" if host else "default"
    
    # 检查缓存是否有效
    if cache_key in server_data_cache and current_time - server_data_cache[cache_key]['timestamp'] < cache_expiry:
        return server_data_cache[cache_key]['data']
    
    # 缓存无效，重新获取数据
    results = {}
    
    # 定义要执行的命令
    commands = {
        "cpu": "top -b -n 1 | head -n 5",
        "memory": "free -h",
        "disk": "df -h",
        "load": "uptime"
    }
    
    # 直接执行命令
    for key, cmd in commands.items():
        try:
            if host:
                code, out, err = run_ssh_command(cmd, host, port, username, password)
            else:
                code, out, err = run_ssh_command(cmd)
            results[key] = out
        except Exception as e:
            results[key] = f"获取数据失败: {e}"
    
    # 更新缓存
    if cache_key not in server_data_cache:
        server_data_cache[cache_key] = {}
    server_data_cache[cache_key]['data'] = results
    server_data_cache[cache_key]['timestamp'] = current_time
    
    return results


@app.post("/api/chat")
def api_chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    AI聊天接口（混合模式）：
    - 支持自然语言和Linux命令两种输入方式
    - 自然语言通过DeepSeek API转换为Linux命令
    - Linux命令直接执行
    - 执行命令并返回结果
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    # 获取最新的用户消息
    latest_message = req.messages[-1]
    if latest_message.role != "user":
        raise HTTPException(status_code=400, detail="最新消息必须是用户消息")

    # 获取服务器信息
    if req.server_id:
        db_server = db.query(Server).filter(Server.id == req.server_id).first()
        if not db_server:
            raise HTTPException(status_code=404, detail="服务器不存在")
        host = db_server.host
        port = db_server.port
        username = db_server.username
        password = db_server.password
    else:
        # 使用默认服务器
        db_server = db.query(Server).first()
        if not db_server:
            raise HTTPException(status_code=404, detail="没有可用的服务器")
        host = db_server.host
        port = db_server.port
        username = db_server.username
        password = db_server.password

    try:
        # 测试服务器连接
        from ssh_client import test_server_connection
        is_connected = test_server_connection(host, port, username, password)
        if not is_connected:
            response = f"无法连接到服务器 {host}:{port}，请检查服务器状态和连接信息。"
            # 更新服务器状态
            db_server.status = "offline"
            db.commit()
            return {"reply": response, "server_id": db_server.id, "server_name": db_server.name}
        
        # 获取最新的用户消息内容
        user_input = latest_message.content
        
        # 判断是自然语言还是Linux命令
        if is_linux_command(user_input):
            # 直接执行Linux命令
            cmd = user_input
            print(f"检测到Linux命令，直接执行: {cmd}")
        else:
            # 调用DeepSeek API将自然语言转换为命令
            print(f"检测到自然语言，调用DeepSeek API转换: {user_input}")
            try:
                system_prompt = """
                你是一个专业的Linux运维助手，负责将用户的自然语言需求转换为准确的Linux命令。
                
                规则：
                1. 只返回命令本身，不要包含任何解释
                2. 如果无法确定命令，返回'无法确定命令'
                3. 命令要安全、准确、高效
                4. 优先使用常用命令
                5. 如果需要查看文件内容，使用cat命令
                6. 如果需要搜索文件，使用find或grep命令
                7. 如果需要查看进程，使用ps命令
                8. 如果需要查看网络连接，使用netstat或ss命令
                """
                messages = [{"role": "user", "content": f"请将以下需求转换为Linux命令：\n\n{user_input}"}]
                cmd = get_ai_response(messages, system_prompt)
                
                # 检查命令是否有效
                if cmd.strip() == "无法确定命令":
                    response = "抱歉，我无法理解您的需求，请尝试更详细地描述，或者直接输入Linux命令。"
                    # 更新服务器状态
                    db_server.status = "online"
                    db_server.last_connected = datetime.utcnow()
                    db.commit()
                    return {"reply": response, "server_id": db_server.id, "server_name": db_server.name}
                
                print(f"DeepSeek API转换结果: {cmd}")
            except Exception as ai_error:
                # 如果 API 调用失败，提示用户直接输入命令
                print(f"DeepSeek API 调用失败: {ai_error}")
                response = f"抱歉，AI转换失败，请直接输入Linux命令。错误信息：{ai_error}"
                # 更新服务器状态
                db_server.status = "online"
                db_server.last_connected = datetime.utcnow()
                db.commit()
                return {"reply": response, "server_id": db_server.id, "server_name": db_server.name}
        
        # 检查命令安全性
        if not is_command_safe(cmd):
            response = f"命令 '{cmd}' 被安全策略阻止，可能存在安全风险。请检查命令是否包含危险操作。"
            # 更新服务器状态
            db_server.status = "online"
            db_server.last_connected = datetime.utcnow()
            db.commit()
            return {"reply": response, "server_id": db_server.id, "server_name": db_server.name}
        
        # 执行命令
        print(f"执行命令: {cmd}")
        code, out, err = run_ssh_command(cmd, host, port, username, password)
        
        # 构建响应
        if code == 0:
            response = f"执行命令 `{cmd}` 结果：\n\n{out}"
        else:
            response = f"执行命令 `{cmd}` 失败（退出码：{code}）：\n\n{out}\n\n错误信息：\n{err}"
        
        # 保存命令执行历史
        try:
            db_command = Command(
                server_id=db_server.id,
                command=cmd,
                output=out,
                exit_code=code,
                executed_by="user"
            )
            db.add(db_command)
            db.commit()
        except Exception as log_error:
            print(f"保存命令执行历史失败: {log_error}")
        
        # 更新服务器状态
        db_server.status = "online"
        db_server.last_connected = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        response = f"抱歉，执行命令时出现错误：{e}"
        print(f"执行命令时出现错误: {e}")
        import traceback
        traceback.print_exc()
        # 更新服务器状态
        if db_server:
            db_server.status = "offline"
            db.commit()

    return {"reply": response, "server_id": db_server.id, "server_name": db_server.name}


if __name__ == "__main__":
    # 初始化数据库
    try:
        create_tables()
        init_default_server()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
    
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
