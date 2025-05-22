from dataclasses import dataclass
from enum import Enum

class Module(Enum):
    API = 0
    DISCORD = 1

class MessageType(Enum):
    EMPTY = 0

@dataclass
class MessageData:
    type: MessageType
    #callback:

@dataclass
class Message:
    sender: Module
    reciever: Module
    content: MessageData
