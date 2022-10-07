import re
from collections import deque
from socket import AF_INET6, create_server

from channel import Channel
from client import Client

from config import HOST, PORT
from message import Message


SHOULD_STOP = False
CLIENT: Client | None = None

RE_NICKNAME = re.compile(r"[A-Za-z][A-Za-z\d\[\]\\\`\_\^\{\|\}]{0,8}")



class Server:
    name: str  # [1..64]
    channels: dict[str, Channel]  # {channel_name: Channel}
    # TODO: store Message?
    # TODO: store these messages with a user? might be useful with async
    # Mutliple messages can arrive at the same time, they have to be stored somewhere for processing
    queue: deque[str]

    def __init__(self, name: str = "SERVER") -> None:
        self.name = name
        self.channels = {}
        self.queue = deque()

    def run(self) -> None:
        try:
            with create_server((HOST, PORT), family=AF_INET6) as s:
                conn, addr = s.accept()
                CLIENT = Client(conn)
                print(f"Connection from {addr}")
                data: str = ""
                while not SHOULD_STOP:
                    data = data + CLIENT.conn.recv(512).decode("UTF-8")
                    # print(f"MSG FROM {conn}: {len(data)} {data}, {msg}")
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

                    # TODO: deque might not be needed here, can use a list instead
                    for msg in self.queue:
                        self.handle_message(CLIENT, msg.split(" "))
                    self.queue = deque()

        except KeyboardInterrupt:
            print("CTRL-C received.")

    def handle_message(self, user: Client, msg: list[str]) -> None:
        if len(msg) == 0:
            return

        # TODO: I have misunderstood what the prefix does, should probably investigate and fix
        # Message starts with a prefix
        # if msg[0][0] == ":":
        #    user.prefix = msg[0][1:]
        #    msg.pop(0)

        # TODO: create a message class which will store necessary data and handle the command processing
        msg[0] = msg[0].upper()
        match msg[0]:
            case "NICK":
                self.cmd_NICK(user, msg)
            case "USER":
                self.cmd_USER(user, msg)
            case "PING":
                self.cmd_PING(user, msg)

            case "CAP":
                pass

            case _:
                print(f"[CMD][NOT_HANDLED] {msg}")
                # TODO: the docs say it should be returned to "a registered cliend". should check for auth?
                user.send_command(Message.ERR_UNKNOWNCOMMAND(msg[0]))

    def cmd_NICK(self, user: Client, msg: list[str]) -> None:
        if len(msg) < 2:
            user.send_command(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        nickname = msg[1][:9]
        if RE_NICKNAME.fullmatch(nickname):
            user.nickname = nickname
            print(f"[CMD][NICK] SET VALID NAME \"{nickname}\"")
        else:
            # TODO: handle invalid name
            pass

        if user.is_authenticated:
            user.send_command(Message.user_greeting(user))

    def cmd_USER(self, user: Client, msg: list[str]) -> None:
        if len(msg) < 5:
            user.send_command(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        # TODO: validation of all fields
        user.username = msg[1]

        try:
            mode = int(msg[2])
            user.mode = (bool(mode & 2), bool(mode & 8))
        except ValueError:
            # TODO: handle invalid modes
            pass

        if msg[4].startswith(":"):
            user.realname = ' '.join(msg[4:])[1:]
        else:
            user.realname = msg[4]

        print(f"[CMD][USER] SET USER \"{user.username}\", w={user.mode[0]}, i={user.mode[1]}, {user.realname}")
        if user.is_authenticated:
            user.send_command(Message.user_greeting(user))

    def cmd_PING(self, user: Client, msg: list[str]) -> None:
        # TODO: this is a placeholder
        user.send_command(Message.CMD_PONG(msg[1]))


if __name__ == "__main__":
    print("Started...")

    server = Server()
    server.run()
