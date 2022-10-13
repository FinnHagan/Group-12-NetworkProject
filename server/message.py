from config import HOSTNAME, VER
from client import Client


class Message:

    @staticmethod
    def user_greeting(client: Client) -> str:
        return f":{HOSTNAME} ".join([
            Message.RPL_WELCOME(client),
            Message.RPL_YOURHOST(),
            Message.RPL_CREATED(),
            Message.RPL_MYINFO(client),
            Message.ERR_NOMOTD()
        ])

    @staticmethod
    def RPL_WELCOME(client: Client) -> str:
        return f"001 {client.nickname} :Welcome to the Internet Relay Network {client.nickname}!{client.username}@{HOSTNAME}\r\n"

    @staticmethod
    def RPL_YOURHOST() -> str:
        return f"002 Your host is {HOSTNAME}, running version {VER}\r\n"

    @staticmethod
    def RPL_CREATED() -> str:
        return "003 This server was created sometime\r\n"

    @staticmethod
    def RPL_MYINFO(client: Client) -> str:
        return f"004 {HOSTNAME} {VER} o o\r\n"

    @staticmethod
    def RPL_LUSERCLIENT() -> str:
        # TODO: correct number of users
        return "251 :There are 1 users and 0 services on 1 servers\r\n"

    @staticmethod
    def ERR_UNKNOWNCOMMAND(command: str) -> str:
        return f"421 {command.upper()} :Unknown command\r\n"

    @staticmethod
    def ERR_NOMOTD() -> str:
        return "422 :MOTD File is missing\r\n"

    @staticmethod
    def ERR_NEEDMOREPARAMS(command: str) -> str:
        return f"461 {command.upper()} :Not enough parameters\r\n"

    @staticmethod
    def CMD_PONG(target: str) -> str:
        # TODO: I don't think this is how it works
        return f"PONG {HOSTNAME} :{target}\r\n"
