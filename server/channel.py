from client import Client


class Channel:
    name: str
    # TODO: this should probably be a {username: (modes, etc.)} dictionary
    users: set[Client]
    topic: str

    def __init__(self, name: str, topic: str = "") -> None:
        self.name = name
        self.topic = topic
        self.users = set()

    def add_user(self, user: Client) -> None:
        self.users.add(user)

    def remove_user(self, user: Client) -> None:
        self.users.remove(user)
