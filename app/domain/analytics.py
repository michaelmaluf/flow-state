from dataclasses import dataclass, field
from app.domain.enums import TimeFrame
from app.domain.models import ApplicationView


@dataclass
class AnalyticsReport:
    time_frame: TimeFrame
    overall_time: float
    productive_time: float
    non_productive_time: float
    productive_time_breakdown: list[ApplicationView] = field(default_factory=list)
    non_productive_time_breakdown: list[ApplicationView] = field(default_factory=list)
