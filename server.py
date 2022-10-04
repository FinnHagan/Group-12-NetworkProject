from socket import AF_INET6, create_server
from collections import deque
import re

HOST = "::1"
PORT = 6667
SHOULD_STOP = False

CLIENT = None

RE_NICKNAME = re.compile(r"[A-Za-z][A-Za-z\d\[\]\\\`\_\^\{\|\}]{0,8}")


class User:
    nickname: str  # [1..10]
    username: str
    realname: str
    op: bool
    mode: tuple[bool, bool]


class Channel:
    users: list[User]


class Message:
    pass


class Server:
    name: str  # [1..64]
    channels: dict[str, Channel]  # {channel_name: Channel}
    # TODO: store Message
    queue: deque[str]

    def __init__(self, name: str = "SERVER") -> None:
        self.name = name
        self.channels = {}
        self.queue = deque()

    def run(self) -> None:
        try:
            with create_server((HOST, PORT), family=AF_INET6) as s:
                conn, addr = s.accept()
                CLIENT = (conn, addr, User())
                print(f"Connection from {addr}")
                data: str = ""
                while not SHOULD_STOP:
                    data = data + CLIENT[0].recv(512).decode("UTF-8")
                    #print(f"MSG FROM {conn}: {len(data)} {data}, {msg}")
                    # There can be multiple '\r\n' separated messages in one chunk of data
                    messages: list[str] = data.split("\r\n")
                    # Add messages to the processing queue
                    self.queue.extend(messages[:-1])
                    # Handle the possibility that the last message is incomplete
                    if messages[-1] == "":
                        data = ""
                    else:
                        # Leave the last message in the current chunk for later
                        data = data + messages[-1]

                    print(self.queue)
                    # TODO: deque might not be needed here, can use a list instead
                    for msg in self.queue:
                        self.handle_message(CLIENT[2], msg.split(" "))
                    self.queue = deque()

        except KeyboardInterrupt:
            print("CTRL-C received.")

    def handle_message(self, user: User, msg: list[str]) -> None:
        if len(msg) == 0:
            return
        prefix: str | None = None

        # Message starts with a prefix
        if msg[0][0] == ":":
            prefix = msg[0][1:]
            msg.pop(0)

        # TODO: create a class message which will store necessary data and handle the command processing
        match msg[0]:
            case "NICK":
                self.cmd_nick(user, msg)
            case "USER":
                self.cmd_user(user, msg)
                
            case _:
                # TODO: no command match
                print(f"[CMD][NOT_HANDLED] {msg}")

    def cmd_nick(self, user: User, msg: list[str]) -> None:
        nickname = msg[1][:9]
        if RE_NICKNAME.fullmatch(nickname):
            user.nickname = nickname
            print(f"[CMD][NICK] SET VALID NAME \"{nickname}\"")
        else:
            # TODO: handle invalid name
            pass

    def cmd_user(self, user: User, msg: list[str]) -> None:
        # TODO: validation of all fields
        user.username = msg[1]
        
        try:
            mode = int(msg[2])
            user.mode = (bool(mode & 2), bool(mode & 8))
        except ValueError:
            # TODO: handle invalid modes
            pass
        
        # TODO: does the realname always start with ':'?
        user.realname = ' '.join(msg[4:])[1:]

        print(f"[CMD][USER] SET USER \"{user.username}\", w={user.mode[0]}, i={user.mode[1]}, {user.realname}")




if __name__ == "__main__":
    print("Started...")

    server = Server()
    server.run()
