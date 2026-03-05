<<<<<<< HEAD
# 内网运维助手

一个基于FastAPI和DeepSeek API的智能内网运维助手，支持自然语言和Linux命令两种输入方式，可用于服务器管理和监控。

## 功能特性

- **混合模式输入**：支持自然语言和Linux命令两种输入方式
- **智能命令转换**：通过DeepSeek API将自然语言转换为Linux命令
- **安全策略**：内置危险命令检测和安全检查机制
- **服务器管理**：支持多服务器管理和状态监控
- **快捷操作**：提供CPU、内存、磁盘、负载等系统信息的快捷查询
- **命令执行**：支持在远程服务器上执行命令并返回结果
- **系统监控**：实时监控服务器状态和性能

## 技术栈

- **后端**：FastAPI、Python 3.8+
- **前端**：HTML5、CSS3、JavaScript
- **数据库**：SQLite
- **API**：DeepSeek API
- **网络**：SSH

## 安装说明

### 1. 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- 网络连接（用于访问DeepSeek API）

### 2. 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/intranet-ops-assistant.git
   cd intranet-ops-assistant
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置服务器信息**
   编辑 `config.py` 文件，添加服务器信息：
   ```python
   # 服务器配置
   SERVERS = [
       {
           "id": 1,
           "name": "默认服务器",
           "host": "192.168.108.131",
           "port": 22,
           "username": "beeplux",
           "password": "Bp20220726;"
       }
   ]

   # DeepSeek API 配置
   DEEPSEEK_API_KEY = "sk-bc3bf884dc2f44518881924ce2af870c"
   DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
   ```

4. **启动服务**
   - 使用一键启动脚本：
     ```bash
     # Windows
     .\一键启动.ps1
     # 或
     .\一键启动.bat
     ```
   - 手动启动：
     ```bash
     python -m uvicorn app:app --host 0.0.0.0 --port 9002
     ```

## 使用方法

1. **访问前端界面**
   打开浏览器，访问：http://localhost:9002/static/index.html

2. **使用自然语言**
   在输入框中输入自然语言，例如：
   - "查看CPU使用率"
   - "ping一下百度官网"
   - "检查内存使用情况"

3. **使用Linux命令**
   切换到"Linux命令"模式，直接输入Linux命令，例如：
   - `ls -la`
   - `ps aux | grep python`
   - `df -h`

4. **使用快捷操作**
   点击左侧的快捷操作按钮，快速查看系统信息：
   - 查看CPU使用情况
   - 查看内存使用情况
   - 查看磁盘使用情况
   - 查看系统负载

## 安全策略

系统内置了安全策略机制，防止危险命令的执行：

- **危险命令黑名单**：阻止已知的危险命令
- **危险命令组合检查**：防止危险命令组合
- **关键文件保护**：保护系统关键文件
- **管道和命令替换限制**：对复杂命令进行严格检查

详细的安全策略说明请参考 `安全策略.md` 文件。

## 项目结构

```
intranet-ops-assistant/
├── app.py              # 主应用文件
├── ai_client.py        # DeepSeek API 客户端
├── ssh_client.py       # SSH 客户端
├── database.py         # 数据库操作
├── config.py           # 配置文件
├── requirements.txt    # 依赖文件
├── static/             # 前端文件
│   └── index.html      # 前端界面
├── 一键启动.bat        # Windows 启动脚本
├── 一键启动.ps1        # PowerShell 启动脚本
├── 操作命令手册.md      # 操作命令手册
├── 技术博客.md         # 技术博客
├── 多机器管理功能规划.md # 多机器管理功能规划
└── 安全策略.md         # 安全策略文档
```

## API 接口

### 1. AI 聊天接口
- **URL**：`/api/chat`
- **方法**：POST
- **参数**：
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "查看CPU使用率"
      }
    ],
    "server_id": 1
  }
  ```
- **返回**：
  ```json
  {
    "reply": "CPU使用率：10.5%",
    "server_id": 1,
    "server_name": "默认服务器"
  }
  ```

### 2. 服务器列表接口
- **URL**：`/api/servers`
- **方法**：GET
- **返回**：
  ```json
  {
    "servers": [
      {
        "id": 1,
        "name": "默认服务器",
        "host": "192.168.108.131",
        "port": 22,
        "status": "online"
      }
    ]
  }
  ```

## 常见问题

1. **启动失败**：检查端口9002是否被占用，使用一键启动脚本会自动停止占用端口的进程。

2. **DNS解析失败**：检查服务器的DNS配置，确保网络连接正常。

3. **命令被安全策略阻止**：检查命令是否包含危险操作，或调整安全策略配置。

4. **DeepSeek API 调用失败**：检查API密钥是否正确，网络连接是否正常。

## 故障排查

1. **查看日志**：启动服务时，控制台会显示详细的日志信息。

2. **测试API**：使用 `test_api.py` 脚本测试API接口。

3. **检查网络**：确保服务器网络连接正常，DNS配置正确。

4. **检查权限**：确保用户有足够的权限执行命令。

## 贡献

欢迎贡献代码和提出建议！请提交Pull Request或Issue。

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 作者：[Your Name]
- 邮箱：[your.email@example.com]
- GitHub：[https://github.com/yourusername/intranet-ops-assistant](https://github.com/yourusername/intranet-ops-assistant)
=======
# intranet-ops-assistant
内网运维助手是一个基于FastAPI和SSH的内网服务器管理工具，通过Web界面实现对多台远程Linux服务器的监控和管理。该系统提供了类似Coze的聊天界面，用户可以通过自然语言指令执行各种运维操作，如查看CPU、内存、磁盘使用情况等。系统支持多机器管理，通过SQLite数据库存储服务器信息。
>>>>>>> f77735e07d8efe1a00b28e64125f6bbb6ae4f50c
