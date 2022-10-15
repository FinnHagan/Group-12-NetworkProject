from socket import socket
import config
import log


class Client:
    conn: socket
    nickname: str = "*"  # [1..10]
    username: str = ""
    realname: str = ""
    op: bool = False
    mode: tuple[bool, bool]

    def __init__(self, conn: socket) -> None:
        self.conn = conn

    @property
    # TODO: refactor this function. Remove default values and use something that makes sense
    def is_authenticated(self) -> bool:
        # TODO: check auth requirements
        return self.nickname != "*" and self.username != ""

    def send_prefix(self, data: str) -> None:
        '''Sends a string to the user. Adds a server prefix.'''
        log.debug(f"[SEND_PREFIX] SENDING {self.nickname=} {data=}")

        self.conn.send(f":{config.HOSTNAME} {data}".encode("UTF-8"))

    # TODO: implement a command which sends list[str]
    def send(self, data: str) -> None:
        '''Sends a string to the user. Does not add a prefix.'''
        log.debug(f"[SEND] SENDING {self.nickname=} {data=}")

        self.conn.send(data.encode("UTF-8"))
