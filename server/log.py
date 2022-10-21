import config


def debug(s: str, end: str = '\n') -> None:
    if config.DEBUG:
        print(s, end=end)
