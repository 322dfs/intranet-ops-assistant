from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


class Server(Base):
    """
    服务器模型
    """
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)  # 实际项目中应该加密存储
    group = Column(String(100), default="其他")
    description = Column(Text, nullable=True)
    status = Column(String(50), default="offline")
    last_connected = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Command(Base):
    """
    命令执行历史模型
    """
    __tablename__ = "commands"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False)
    command = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)
    executed_by = Column(String(255), default="system")


# 创建表
def create_tables():
    Base.metadata.create_all(bind=engine)


# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化默认服务器
def init_default_server():
    from config import DEFAULT_SSH_HOST, DEFAULT_SSH_PORT, DEFAULT_SSH_USER, DEFAULT_SSH_PASSWORD
    
    db = SessionLocal()
    try:
        # 检查是否已有服务器
        existing_server = db.query(Server).first()
        if not existing_server:
            # 创建默认服务器
            default_server = Server(
                name="默认服务器",
                host=DEFAULT_SSH_HOST,
                port=DEFAULT_SSH_PORT,
                username=DEFAULT_SSH_USER,
                password=DEFAULT_SSH_PASSWORD,
                group="生产环境",
                description="默认测试服务器"
            )
            db.add(default_server)
            db.commit()
            print("默认服务器已创建")
    finally:
        db.close()