import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from automate.main import app


def get_config(env: str) -> Config:
    config = Config()

    if env == "dev":
        config.bind = ["127.0.0.1:8000"]
        config.use_reloader = True
        config.reload_dir = "src"
        config.loglevel = "debug"
    elif env == "prod":
        config.bind = ["0.0.0.0:8000"]
        config.workers = 4  # 멀티프로세스
        config.loglevel = "info"
        config.use_reloader = False

    return config


def run(env: str):
    config = get_config(env)
    print(f"mode: {env}")
    asyncio.run(serve(app, config))
