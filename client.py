from socket import socket


class Client:
    conn: socket
    nickname: str  # [1..10]
    username: str
    realname: str
    op: bool
    mode: tuple[bool, bool]

    def __init__(self, conn: socket) -> None:
        self.conn = conn

    @property
    def is_authenticated(self) -> bool:
        # TODO: check whether a user is authenticated (has nickname username anythingelse?)D
        pass

    def send(self, data: str) -> None:
        self.conn.send(data.encode("UTF-8"))
