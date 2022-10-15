import config
from client import Client
from channel import Channel


class Message:

    @staticmethod
    def user_greeting(client: Client, user_count: int = 0) -> str:
        # TODO: should be refactored. Could add a funciton to Client which takes an array of strings and adds prefixes.
        return f":{config.HOSTNAME} ".join([
            Message.RPL_WELCOME(client),
            Message.RPL_YOURHOST(client),
            Message.RPL_CREATED(client),
            Message.RPL_MYINFO(client),
            Message.RPL_LUSERCLIENT(client, user_count),
            Message.ERR_NOMOTD(client)
        ])

    @staticmethod
    def RPL_WELCOME(client: Client) -> str:
        return f"001 {client.nickname} :Welcome to the Internet Relay Network {client.nickname}!{client.username}@{config.HOSTNAME}\r\n"

    @staticmethod
    def RPL_YOURHOST(client: Client) -> str:
        return f"002 {client.nickname} :Your host is {config.HOSTNAME}, running version {config.VER}\r\n"

    @staticmethod
    def RPL_CREATED(client: Client) -> str:
        return f"003 {client.nickname} :This server was created sometime\r\n"

    @staticmethod
    def RPL_MYINFO(client: Client) -> str:
        return f"004 {client.nickname} {config.HOSTNAME} {config.VER} o o\r\n"

    @staticmethod
    def RPL_LUSERCLIENT(client: Client,
                        user_count: int = 0,
                        service_count: int = 0,
                        server_count: int = 1) -> str:
        return f"251 {client.nickname} :There are {user_count} users and {service_count} services on {server_count} servers\r\n"

    @staticmethod
    def RPL_ENDOFWHO(client: Client, channel: Channel) -> str:
        return f"315 {client.nickname} {channel.name} :End of WHO list\r\n"

    @staticmethod
    def RPL_NOTOPIC(client: Client, channel: Channel) -> str:
        return f"331 {client.nickname} {channel.name} :No topic is set\r\n"

    @staticmethod
    def RPL_TOPIC(client: Client, channel: Channel) -> str:
        return f"332 {client.nickname} {channel.name} :{channel.topic}\r\n"

    @staticmethod
    def RPL_WHOREPLY(client: Client, who_client: Client,
                     channel: Channel) -> str:
        # TODO: client address
        return f"352 {client.nickname} {channel.name} {who_client.nickname} ::1 {config.HOSTNAME} {who_client.username} H :0 {client.realname}\r\n"

    @staticmethod
    def ERR_UNKNOWNCOMMAND(command: str) -> str:
        return f"421 {command.upper()} :Unknown command\r\n"

    @staticmethod
    def ERR_NOMOTD(client: Client) -> str:
        return f"422 {client.nickname} :MOTD File is missing\r\n"

    @staticmethod
    def ERR_ERRONEUSNICKNAME(client: Client, name: str) -> str:
        return f"432 {client.nickname} {name} :Erroneous nickname\r\n"

    @staticmethod
    def ERR_NICKNAMEINUSE(client: Client, name: str) -> str:
        return f"433 {client.nickname} {name} :Nickname is already in use\r\n"

    @staticmethod
    def ERR_NEEDMOREPARAMS(command: str) -> str:
        return f"461 {command.upper()} :Not enough parameters\r\n"

    @staticmethod
    def CMD_PONG(target: str) -> str:
        # TODO: I don't think this is how it works
        return f"PONG {config.HOSTNAME} :{target}\r\n"

    @staticmethod
    def CMD_JOIN(client: Client, channel: str) -> str:
        # TODO: client address
        return f":{client.nickname}!{client.username}@::1 JOIN {channel}\r\n"
