from client import Client


# TODO: a channel is pretty much a user? might want to make it a subclass
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
