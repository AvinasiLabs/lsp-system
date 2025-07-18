from typing import Optional, Literal, Dict
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


BASE_PATH = Path(__file__).parent.parent


# Init cache directory
CACHE = BASE_PATH.joinpath('.cache')


# Logger config
class LoggerConfig(BaseSettings):
    name: str
    file_name: str = 'sponge-algo.log'
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'DEBUG'
    when: str = 'midnight'    # S-Seconds, M-Minutes, H-Hours, D-Days, midnight, W{0-6}-certain day
    interval: int = 1
    backup_count: int = 30
    delay: bool = False
    utc: bool = True


class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LLM_", extra="allow")

    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    api_key: SecretStr
    completion_cost: float = 1e-5    # The cost of completion tokens
    prompt_cost: float = 2.5e-6        # The cost of prompt tokens
    proxy: Optional[str] = None
    timeout: float = 300.0
    system_prompt: Optional[str] = None


class BaseMemoryConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MEMORY_", extra="ignore")

    persist_directory: str = str(CACHE.joinpath("memory/default"))
    embedding_model_name: str = "all-MiniLM-L6-v2"
    collection_name: str = "default"
    bm25_data_file: str = "bm25_data.pkl"


# Store config
class PostgreSQLConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="POSTGRES_", extra="ignore")

    dbname: str
    user: str
    pwd: SecretStr
    host: str
    port: int
    min_connections: int = 1
    max_connections: int = 10


class APIConfig(BaseSettings):
    """API配置"""
    model_config = SettingsConfigDict(env_file=".env", env_prefix="API_", extra="ignore")
    
    # 认证系统开关
    auth_enabled: bool = False
    
    # JWT设置（仅在auth_enabled=True时使用）
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24小时
    
    # 服务器设置
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS设置
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]