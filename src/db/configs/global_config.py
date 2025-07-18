from .config_cls import (
    LoggerConfig,
    PostgreSQLConfig,
    APIConfig
)


LOGGER_CONFIG = LoggerConfig(
    name="sponge-algo",
    file_name="sponge-algo.log",
    level="INFO",
    when="midnight",
    interval=1,
    backup_count=90,
    delay=False,
    utc=True
)


POSTGRES_CONFIG = PostgreSQLConfig(
    min_connections=1,
    max_connections=10
)


API_CONFIG = APIConfig()
