import enum


class AccountabilityState(enum.Enum):
    PRODUCTIVE = 'productive'
    NON_PRODUCTIVE = 'non_productive'
    POMODORO = 'pomodoro'