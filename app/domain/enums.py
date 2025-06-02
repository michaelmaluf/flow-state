import enum


class FlowStateStatus(enum.Enum):
    INACTIVE = 1
    ACTIVE = 2
    SHUTDOWN = 3


class ProductivityState(enum.Enum):
    IDLE = 1
    PRODUCTIVE = 2
    NON_PRODUCTIVE = 3
    POMODORO = 4

class TimeFrame(enum.Enum):
    TODAY = 1
    WEEK = 2
    MONTH = 3
    ALL = 4