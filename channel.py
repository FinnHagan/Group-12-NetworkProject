from client import Client


# TODO: a channel is pretty much a user? might want to make it a subclass
class Channel:
    users: list[Client]
