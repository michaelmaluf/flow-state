from collections import defaultdict
from datetime import datetime, date
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Application(BaseModel):
    id: Optional[int]
    name: str
    is_productive: bool
    tag: str = ''
    # start_time: Optional[datetime] = Field(default_factory=datetime.now)
    elapsed_time: int = 0

    model_config = ConfigDict(
        from_attributes=True,
    )

    def is_match(self, app_name: str, tag: str = '') -> bool:
        return app_name == self.name and tag == self.tag

    def __eq__(self, other):
        if isinstance(other, Application):
            return self.id == other.id
        return NotImplemented

    def __hash__(self):
        return hash(self.id) if self.id is not None else hash((self.name, self.tag))

    def __repr__(self):
        return f"<Application(name='{self.name}', productivity={self.is_productive}, tag={self.tag})>"


class WorkdayApplication(BaseModel):
    id: Optional[int] = None
    workday_id: int
    application_id: int
    time_seconds: int
    application: Optional[Application] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class Workday(BaseModel):
    id: int
    date: date
    pomodoros_left: int
    workday_applications: list[WorkdayApplication]
    productive_time_seconds: int = 0
    non_productive_time_seconds: int = 0
    # workday_applications: Optional[list[WorkdayApplication]] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True
    )

    def model_post_init(self, __context):
        for wa in self.workday_applications:
            if wa.application.is_productive:
                self.productive_time_seconds += wa.time_seconds
            else:
                self.non_productive_time_seconds += wa.time_seconds



class Session(BaseModel):
    id: Optional[int] = None
    workday_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    interruption_count: int = 0
    idle_time: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )

    @classmethod
    def to_dict(cls, session) -> Dict[str, Any]:
        data = session.model_dump(exclude_none=True)

        if "idle_time" in data:
            del data["idle_time"]

        return data

    def __repr__(self):
        return (
            f"Session(id={self.id}, workday_id={self.workday_id}, "
            f"start_time={self.start_time!r}, end_time={self.end_time!r}, "
            f"interruption_count={self.interruption_count}, idle_time={self.idle_time!r})"
        )


class ScriptResponse(BaseModel):
    app_type: str
    app_name: str
    tag: Optional[str] = ''

    @field_validator('app_name')
    @classmethod
    def normalize_app_name(cls, v):
        return v.strip().lower() if v else v

    @classmethod
    def from_arr(cls, *args):
        return ScriptResponse(
            app_type=args[0],
            app_name=args[1],
            tag=args[2] if len(args) >= 3 else ''
        )

    def __repr__(self):
        return f"ScriptResponse(app_type={self.app_type}, app_name={self.app_name}, tag={self.tag}"


class ApplicationView(BaseModel):
    name: str
    is_productive: bool
    elapsed_time: Optional[int] = 0
    percent_usage: Optional[float] = 0

    def __eq__(self, other):
        if isinstance(other, ApplicationView):
            return self.name == other.name and self.is_productive == other.is_productive
        return NotImplemented

    def __repr__(self):
        return f"<Application(name='{self.app.name}', productivity={self.is_productive}, elapsed_time={self.elapsed_time})>"
