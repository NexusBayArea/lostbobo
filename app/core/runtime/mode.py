from enum import Enum


class RuntimeMode(str, Enum):
    API = "api"
    WORKER = "worker"
    CI = "ci"
    DEV = "dev"
