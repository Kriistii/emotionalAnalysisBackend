import os


def safe_open(path, type):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, type)
