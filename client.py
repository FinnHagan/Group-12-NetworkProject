from socket import socket
import config


class Client:
    conn: socket
    nickname: str = ""  # [1..10]
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
        return self.nickname != "" and self.username != ""

    def send_command(self, data: str) -> None:
        print(f"[SEND_COMMAND] SENDING to {self.conn=} {self.nickname=} {data=}")

        self.conn.send(f":{config.HOSTNAME} {data}".encode("UTF-8"))
