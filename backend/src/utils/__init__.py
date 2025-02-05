import os


def getenv(key: str, default: str = None):
    env = os.getenv(key, default)
    if default is None and env is None:
        raise RuntimeError(f"The environment variable {env} was not found!")
    return env
