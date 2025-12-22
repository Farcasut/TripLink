from enum import Enum, IntEnum

class UserRole(IntEnum):
    DEFAULT = 1
    DRIVER = 2
    ADMIN = 10

class BookingStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DENIED = "denied"
