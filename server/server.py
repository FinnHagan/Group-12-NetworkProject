import re
import select
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
    clients: dict[str, Client]

    def __init__(self, name: str = "SERVER") -> None:
        self.name = name
        self.channels = {}
        self.clients = {}

    def bind(self, addr: str = "127.0.0.1", port: int = 6667, ipv6: bool = True) -> None:
        # TODO: should probably reset the connections? Or maybe the whole server. Shouldnt be called more than once, so might just move to __init__
        self.server = create_server((addr, port), family=AF_INET6 if ipv6 else AF_INET)

    def run(self) -> None:
        try:
            while True:
                client_conns: list[socket] = [client.conn for client in self.clients.values()]
                # TODO: some clients might have writes blocked, which is what 'w' is for
                # In that case there should probably be a write queue for each client?
                # TODO: store last interaction time for clients and send PING to them. Remove inactive clients.
                # This function returns every __timeout=5 seconds, even if no messages are received. This should be used to check and send PING
                r, _, _ = select.select(client_conns + [self.server], [], [], 5)

                i: socket
                for i in r:
                    if i is self.server:
                        conn, _ = self.server.accept()
                        client = Client(conn)
                        # TODO: the client here should be added to a separate list (set?) of unauthenticated clients
                        self.clients[client.nickname] = client
                        # print(self.clients)
                    else:
                        # Search for the client with current socket
                        # TODO: should handle unauthenticated clients separately. They can not use most of the commands, and must authenticate as soon as possible
                        sender = next(client for client in self.clients.values() if client.conn is i)
                        # TODO: make sure disconnection handling works as it should
                        try:
                            data = i.recv(2048).decode("UTF-8")
                        except ConnectionError as e:
                            print(f"[CLIENT] Connection error while trying to read from {i}: {e}")
                            self.cmd_QUIT(sender, ["QUIT", ":Leaving"])
                            continue

                        sender.update_last_interaction()
                        # There can be multiple '\r\n' separated messages in one chunk of data
                        messages: list[str] = data.split("\r\n")
                        # print(f"MSG FROM {i}: {len(data)} {data}, {messages}")

                        for msg in messages:
                            if msg == "":
                                continue
                            self.handle_message(sender, msg.split(" "))

                self.check_clients()
        except KeyboardInterrupt:
            print("[SERVER] KeyboardInterrupt received. Quitting...")
            self.server.close()

    def check_clients(self) -> None:
        """Checks last interaction time with all clients, sends PING, disconnects unresponsive clients"""
        for client in dict(self.clients).values():      # Check for dead clients
            if not client.is_alive:
                if client.is_pinged:
                    # Client timed out
                    self.cmd_QUIT(client, ["QUIT", ":Timed out"])
                else:
                    client.send_with_prefix(Message.CMD_PING())
                    client.is_pinged = True

    def handle_message(self, sender: Client, msg: list[str]) -> None:
        """Main message handler"""
        if len(msg) == 0 or len(msg[0]) == 0:
            return

        msg[0] = msg[0].upper()
        match msg[0]:
            case "NICK":
                self.cmd_NICK(sender, msg)
            case "USER":
                self.cmd_USER(sender, msg)
            case "PING":
                self.cmd_PING(sender, msg)
            case "QUIT":
                self.cmd_QUIT(sender, msg)
            case "JOIN":
                self.cmd_JOIN(sender, msg)
            case "PART":
                self.cmd_PART(sender, msg)
            case "WHO":
                self.cmd_WHO(sender, msg)
            case "PRIVMSG":
                self.cmd_PRIVMSG(sender, msg)

            case "PONG":
                pass
            case "CAP":
                pass

            case _:
                log.debug(f"[CMD][NOT_HANDLED] {msg}")
                # TODO: the docs say it should be returned to "a registered client". should check for auth?
                sender.send_with_prefix(Message.ERR_UNKNOWNCOMMAND(sender, msg[0]))

    @staticmethod
    def join_message_tail(msg: list[str]) -> str:
        """Joins list of words which are located at the end of a message.
        Returns the first word if there is no ':' symbol.
        Returns the whole line if there is a ':' symbol"""
        message = ' '.join(msg)[1:] if msg[0].startswith(":") else msg[0]
        return message.strip()

    def cmd_NICK(self, sender: Client, msg: list[str]) -> None:
        if len(msg) < 2:
            sender.send_with_prefix(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        nickname = msg[1][:9]
        if RE_NICKNAME.fullmatch(nickname):
            for c in self.clients:
                if nickname.lower() == self.clients[c].nickname.lower():
                    log.debug(f"[CMD][NICK] Tried to set a name that is already taken: {nickname}")
                    sender.send_with_prefix(Message.ERR_NICKNAMEINUSE(sender, nickname))
                    return

            # TODO: if a user changes their name then a response must be sent
            # TODO: avoid greeting users who have already been greeted (which is those who are changing their name)
            if sender.nickname in self.clients:
                del self.clients[sender.nickname]
            sender.nickname = nickname
            self.clients[nickname] = sender
            print(self.clients)
            log.debug(f"[CMD][NICK] SET VALID NAME \"{nickname}\"")
        else:
            # TODO: verify that the regex above is correct and that this response is valid
            log.debug(f"[CMD][NICK] Tried to set an invalid name: {nickname}")
            sender.send_with_prefix(Message.ERR_ERRONEUSNICKNAME(sender, nickname))

        if sender.is_authenticated:
            sender.send_iter_with_prefix(Message.user_greeting(sender, len(self.clients)))

    def cmd_USER(self, sender: Client, msg: list[str]) -> None:
        if len(msg) < 5:
            sender.send_with_prefix(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        # TODO: validation of all fields
        sender.username = msg[1]

        try:
            mode = int(msg[2])
            sender.mode = (bool(mode & 2), bool(mode & 8))
        except ValueError:
            # TODO: handle invalid modes
            pass

        if msg[4].startswith(":"):
            sender.realname = ' '.join(msg[4:])[1:]
        else:
            sender.realname = msg[4]

        log.debug(f"[CMD][USER] SET USER \"{sender.username}\", w={sender.mode[0]}, i={sender.mode[1]}, {sender.realname}")
        if sender.is_authenticated:
            sender.send_iter_with_prefix(Message.user_greeting(sender, len(self.clients)))

    def cmd_PING(self, sender: Client, msg: list[str]) -> None:
        # TODO: this is a placeholder
        sender.send_with_prefix(Message.CMD_PONG(msg[1]))

    def cmd_JOIN(self, sender: Client, msg: list[str]) -> None:
        # TODO: handle invalid command usage (such as no channels given or invalid channel name)
        channels = list(filter(lambda x: x != '', msg[1].split(',')))
        for c in channels:
            self.join_channel(sender, c.lower())
            channel = self.channels[c.lower()]
            for c_user in channel.users:
                c_user.send(Message.CMD_JOIN(sender, c.lower()))

            if channel.topic != "":
                sender.send_with_prefix(Message.RPL_TOPIC(sender, channel))
            else:
                sender.send_with_prefix(Message.RPL_NOTOPIC(sender, channel))

            sender.send_iter_with_prefix([
                Message.RPL_NAMREPLY(sender, channel),
                Message.RPL_ENDOFNAMES(sender, channel)])

    def join_channel(self, sender: Client, channel: str) -> None:
        """Add user to a channel with given name"""
        if channel not in self.channels:
            # TODO: validate channel name
            self.channels[channel] = Channel(channel)
        self.channels[channel].add_user(sender)

    def cmd_PART(self, sender: Client, msg: list[str]) -> None:
        if len(msg) < 2:
            sender.send_with_prefix(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        channels = msg[1].split(',')
        message = self.join_message_tail(msg[2:])

        for c in channels:
            channel = self.channels.get(c.lower())
            if channel is not None:
                if sender in channel.users:
                    part_msg = f"{sender.prefix} PART {channel.name} :{message}"
                    for user in channel.users:
                        user.send(part_msg)
                    channel.remove_user(sender)
                else:
                    # TODO: return ERR_NOTONCHANNEL
                    pass
            else:
                # TODO: return ERR_NOSUCHCHANNEL
                pass

        log.debug(f"[CMD][PART] {sender.username} is leaving channels {msg[1]} with message {message=}")

    def cmd_QUIT(self, sender: Client, msg: list[str]) -> None:
        log.debug(f"[CMD][QUIT] {sender.username} quit with message {msg=}")

        self.remove_client(sender)
        for c in self.channels.values():
            if sender in c.users:
                c.remove_user(sender)

            message = self.join_message_tail(msg[1:])

            quit_msg = f"{sender.prefix} QUIT :{message}"
            for user in c.users:
                user.send(quit_msg)

    def remove_client(self, client: Client) -> None:
        """Remove user from the server"""
        del self.clients[client.nickname]

    def cmd_WHO(self, sender: Client, msg: list[str]) -> None:
        if len(msg) < 2:
            sender.send_with_prefix(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        channel = self.channels.get(msg[1].lower())
        if channel is None:
            sender.send_with_prefix(Message.ERR_NOSUCHSERVER(sender, msg[1].lower()))
            return

        reply = [Message.RPL_WHOREPLY(sender, who_client, channel) for who_client in channel.users]
        reply.append(Message.RPL_ENDOFWHO(sender, channel))
        sender.send_iter_with_prefix(reply)

    def cmd_PRIVMSG(self, sender: Client, msg: list[str]) -> None:
        if len(msg) < 3:
            sender.send_with_prefix(Message.ERR_NEEDMOREPARAMS(msg[0]))
            return

        target = msg[1].lower()
        message = self.join_message_tail(msg[2:])

        for c in self.clients:
            if self.clients[c].nickname.lower() == target:
                target_client = self.clients[c]
                log.debug(f"[CMD][PRIVMSG] Client {sender.nickname} PRIVMSG to {target_client.nickname} {message=}")
                self.send_privmsg_line(sender, target_client, target_client.nickname, message)
                return
        if target in self.channels:
            channel = self.channels[target.lower()]
            log.debug(f"[CMD][PRIVMSG] Client {sender.nickname} PRIVMSG to channel {channel.name} {message=}")
            for target_client in channel.users:
                if target_client != sender:
                    self.send_privmsg_line(sender, target_client, target, message)
        else:
            # TODO: handle invalid target name
            pass

    def send_privmsg_line(self, sender: Client, target_client: Client, target_name: str, message: str) -> None:
        try:
            target_client.send(f"{sender.prefix} PRIVMSG {target_name.lower()} :{message}")
        except ConnectionError as e:
            print(f"[CMD][PRIVMSG] Connection error while trying to send a message to {target_name}: {e}")
            self.cmd_QUIT(target_client, ["QUIT", ":Leaving"])


if __name__ == "__main__":
    print("[SERVER] Started...")

    server = Server()
    server.bind(config.HOST, config.PORT, True)
    server.run()
