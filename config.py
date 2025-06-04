from pydantic_settings import BaseSettings
from pydantic import Json

class Settings(BaseSettings):
    SSH_HOST: str
    SSH_USER: str
    SSH_MASTER_PASSWORD: str
    SSH_WORKER_PASSWORD: str
    SSH_PORT: int

    GIT_USER: str
    GIT_PASSWORD: str
    GIT_URL: str

    SCENARIO_BASE: str
    SSH_WORKER_IPs: str
    API_BASE: str
    PYTHON_PATH: str
    LOCUST_PATH: str

    @property
    def ssh_worker_ips_list(self) -> list[str]:
        return [ip.strip() for ip in self.SSH_WORKER_IPs.split(",")]

    class Config:
        env_file = ".env"

settings = Settings()