import paramiko
from typing import Tuple, Dict

from config import DEFAULT_SSH_HOST, DEFAULT_SSH_PORT, DEFAULT_SSH_USER, DEFAULT_SSH_PASSWORD, SSH_TIMEOUT

# 全局SSH客户端缓存，避免重复建立连接
_ssh_clients: Dict[str, paramiko.SSHClient] = {}


def _get_ssh_client(
    host: str = DEFAULT_SSH_HOST,
    port: int = DEFAULT_SSH_PORT,
    username: str = DEFAULT_SSH_USER,
    password: str = DEFAULT_SSH_PASSWORD,
    timeout: int = SSH_TIMEOUT,
) -> paramiko.SSHClient:
    """
    获取或创建SSH客户端连接
    """
    key = f"{host}:{port}:{username}"
    
    # 检查缓存中是否有可用的客户端
    if key in _ssh_clients:
        client = _ssh_clients[key]
        try:
            # 测试连接是否仍然有效
            client.exec_command("echo test", timeout=2)
            return client
        except:
            # 连接无效，删除缓存
            del _ssh_clients[key]
    
    # 创建新的SSH客户端
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            timeout=timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        # 缓存客户端
        _ssh_clients[key] = client
        return client
    except Exception as e:
        print(f"SSH连接错误: {type(e).__name__}: {e}")
        print(f"连接信息: {host}:{port}, 用户名: {username}")
        raise


def run_ssh_command(
    command: str,
    host: str = DEFAULT_SSH_HOST,
    port: int = DEFAULT_SSH_PORT,
    username: str = DEFAULT_SSH_USER,
    password: str = DEFAULT_SSH_PASSWORD,
    timeout: int = SSH_TIMEOUT,
) -> Tuple[int, str, str]:
    """
    在远程 Linux 服务器上执行命令，返回 (exit_code, stdout, stderr)。
    """
    client = _get_ssh_client(host, port, username, password, timeout)

    try:
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)

        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")

        return exit_code, out, err
    except Exception as e:
        # 打印详细的错误信息
        print(f"SSH命令执行错误: {type(e).__name__}: {e}")
        # 移除失效的客户端
        key = f"{host}:{port}:{username}"
        if key in _ssh_clients:
            del _ssh_clients[key]
        raise


def test_server_connection(host, port, username, password, timeout=SSH_TIMEOUT):
    """
    测试服务器连接
    """
    try:
        client = _get_ssh_client(host, port, username, password, timeout)
        # 执行测试命令
        stdin, stdout, stderr = client.exec_command("echo test", timeout=2)
        exit_code = stdout.channel.recv_exit_status()
        return exit_code == 0
    except:
        return False

