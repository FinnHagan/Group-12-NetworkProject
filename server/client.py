from socket import socket
from typing import Iterable
from time import time_ns
import config
import log


class Client:
    conn: socket
    nickname: str = "*"  # [1..10]
    username: str = ""
    realname: str = ""
    op: bool = False
    mode: tuple[bool, bool]
    last_interaction: int
    is_pinged: bool = False

    def __init__(self, conn: socket) -> None:
        self.conn = conn
        self.last_interaction = time_ns()

    @property
    # TODO: refactor this function. Remove default values and use something that makes sense
    def is_authenticated(self) -> bool:
        # TODO: check auth requirements
        return self.nickname != "*" and self.username != ""

    @property
    def is_alive(self) -> bool:
        return (time_ns() -
                self.last_interaction) < 60 * 1000 * 1000 * 1000  # 60 seconds

    def update_last_interaction(self) -> None:
        self.last_interaction = time_ns()
        self.is_pinged = False

    def send_with_prefix(self, data: str) -> None:
        '''Sends a string to the user. Adds a server prefix.'''
        log.debug(f"[SEND_PREFIX] SENDING TO {self.nickname} {data=}")

        self.conn.send(f":{config.HOSTNAME} {data}\r\n".encode("UTF-8"))

    def send_iter_with_prefix(self, data: Iterable[str]) -> None:
        '''Sends an iterable of strings to the user. Adds a server prefix.'''
        log.debug(f"[SEND_PREFIX_ITER] SENDING TO {self.nickname} {data=}")

        msg = ""
        for s in data:
            msg += f":{config.HOSTNAME} {s}\r\n"

        self.conn.send(msg.encode("UTF-8"))

    def send(self, data: str) -> None:
        '''Sends a string to the user. Does not add a prefix.'''
        log.debug(f"[SEND] SENDING TO {self.nickname} {data=}")

        self.conn.send((data + '\r\n').encode("UTF-8"))

    def send_iter(self, data: Iterable[str]) -> None:
        '''Sends an iterable of strings to the user. Does not add a prefix.'''
        log.debug(f"[SEND_ITER] SENDING TO {self.nickname} {data=}")

        self.conn.send(('\r\n'.join(data) + '\r\n').encode("UTF-8"))

    @property
    def prefix(self) -> str:
        return f":{self.nickname}!{self.username}@{config.HOSTNAME}"
