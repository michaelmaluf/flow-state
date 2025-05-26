from dataclasses import dataclass, field
from enum import Enum

from domain.models import ApplicationView


class TimeFrame(Enum):
    TODAY = 1
    WEEK = 2
    MONTH = 3
    ALL = 4


@dataclass
class AnalyticsReport:
    time_frame: TimeFrame
    overall_time: float
    productive_time: float
    non_productive_time: float
    productive_time_breakdown: list[ApplicationView] = field(default_factory=list)
    non_productive_time_breakdown: list[ApplicationView] = field(default_factory=list)
