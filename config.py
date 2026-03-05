"""
项目名称：内网运维助手（Intranet Ops Assistant）

说明：
- 这里只是配置信息，真实的测试服务器 IP / 账号 / 密码请按实际情况修改。
- 目前你的网段是 192.168.108.x，这里先放一个占位 IP。
"""

# SSH 配置
DEFAULT_SSH_HOST = "192.168.108.131"  # 真实测试服务器 IP
DEFAULT_SSH_PORT = 22
DEFAULT_SSH_USER = "beeplux"    # 真实用户名
DEFAULT_SSH_PASSWORD = "Bp20220726;"  # 真实密码
SSH_TIMEOUT = 10

# DeepSeek API 配置
DEEPSEEK_API_KEY = "sk-bc3bf884dc2f44518881924ce2af870c"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TEMPERATURE = 0.7

# 数据库配置
DATABASE_URL = "sqlite:///./servers.db"

# 服务器分组
SERVER_GROUPS = ["生产环境", "测试环境", "开发环境", "其他"]
