import re
import select
from collections import deque
from socket import AF_INET, AF_INET6, create_server, socket

import config
import log
from channel import Channel
from client import Client
from message import Message

RE_NICKNAME = re.compile(r"[A-Za-z][A-Za-z\d\[\]\\\`\_\^\{\|\}]{0,8}")


class Server:
    server: socket
    name: str  # [1..64]
    channels: dict[str, Channel]  # {channel_name: Channel}
    clients: set[Client]
    # TODO: REMOVE THE QUEUE? might not be necessary at all
    # TODO: store Message?
    # TODO: store these messages with a user? might be useful with async
    # Mutliple messages can arrive at the same time, they have to be stored somewhere for processing
    queue: deque[str]

    def __init__(self, name: str = "SERVER") -> None:
        self.name = name
        self.channels = {}
        self.queue = deque()
        self.clients = set()

    def bind(self, addr: str = "127.0.0.1", port: int = 6667, ipv6: bool = True) -> None:
        # TODO: should probably reset the connections? Or maybe the whole server
        self.server = create_server((addr, port), family=AF_INET6 if ipv6 else AF_INET)

    def run(self) -> None:
        try:
            while True:
                client_conns: list[socket] = [client.conn for client in self.clients]
                # TODO: some clients might have writes blocked, which is what 'w' is for
                # In that case there should probably be a write queue for each client?
                r, _, _ = select.select(client_conns + [self.server], [], [], 15)

                i: socket
                for i in r:
                    if i is self.server:
                        conn, _ = self.server.accept()
                        self.clients.add(Client(conn))
                    else:
                        # Search for the client with current socket
                        sender = next(client for client in self.clients if client.conn is i)

                        # TODO: make sure disconnection handling works as it should
                        try:
                            data = i.recv(512).decode("UTF-8")
                        except ConnectionError as e:
                            log.debug(f"[CLIENT] Connection error while trying to read form {i}: {e}")
                            self.cmd_QUIT(sender, ["QUIT", ":Leaving"])
                            continue

                        # There can be multiple '\r\n' separated messages in one chunk of data
                        messages: list[str] = data.split("\r\n")
                        # print(f"MSG FROM {i}: {len(data)} {data}, {messages}")

                        for msg in messages:
                            if msg == "":
                                continue
                            # TODO: store clients in a dictionary {socket: client}? might make lookup faster
                            self.handle_message(sender, msg.split(" "))

        except KeyboardInterrupt:
            print("[SERVER] KeyboardInterrupt received. Quitting...")

    def handle_message(self, user: Client, msg: list[str]) -> None:
        if len(msg) == 0 or len(msg[0]) == 0:
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
            case "QUIT":
                self.cmd_QUIT(user, msg)

            case "CAP":
                pass

            case _:
                log.debug(f"[CMD][NOT_HANDLED] {msg}")
                # TODO: the docs say it should be returned to "a registered cliend". should check for auth?
                user.send_command(Message.ERR_UNKNOWNCOMMAND(msg[0]))

    def cmd_NICK(self, user: Client, msg: list[str]) -> None:
        if len(msg) < 2:
            user.send_command(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        nickname = msg[1][:9]
        if RE_NICKNAME.fullmatch(nickname):
            for client in self.clients:
                if client.nickname == nickname:
                    log.debug(f"[CMD][NICK] Tried to set a name that is already taken: {nickname}")
                    user.send_command(Message.ERR_NICKNAMEINUSE(user, nickname))
                    return
            else:
                # TODO: if a user changes their name then a response must be sent
                # TODO: avoid greeting users who have already been greeted (which is those who are changing their name)
                user.nickname = nickname
                log.debug(f"[CMD][NICK] SET VALID NAME \"{nickname}\"")
        else:
            # TODO: verify that the regex above is correct and that this response is valid
            log.debug(f"[CMD][NICK] Tried to set an invalid name: {nickname}")
            user.send_command(Message.ERR_ERRONEUSNICKNAME(user, nickname))

        if user.is_authenticated:
            user.send_command(Message.user_greeting(user, len(self.clients)))

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

        log.debug(f"[CMD][USER] SET USER \"{user.username}\", w={user.mode[0]}, i={user.mode[1]}, {user.realname}")
        if user.is_authenticated:
            user.send_command(Message.user_greeting(user, len(self.clients)))

    def cmd_PING(self, user: Client, msg: list[str]) -> None:
        # TODO: this is a placeholder
        user.send_command(Message.CMD_PONG(msg[1]))

    def cmd_QUIT(self, user: Client, msg: list[str]) -> None:
        log.debug(f"[CMD][QUIT] {user.username} quit with message {msg=}")
        # TODO: leave notifications, message handling etc.
        self.remove_client(user)

    def remove_client(self, client: Client) -> None:
        self.clients.remove(client)


if __name__ == "__main__":
    print("[SERVER] Started...")

    server = Server()
    server.bind(config.HOST, config.PORT, True)
    server.run()
