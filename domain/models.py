from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class Application(BaseModel):
    id: Optional[int]
    name: str
    is_productive: bool
    tag: str = ''
    start_time: Optional[datetime] = Field(default_factory=datetime.now)

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


class Workday(BaseModel):
    id: int
    date: datetime
    pomodoros_left: int
    productive_time_seconds: int
    non_productive_time_seconds: int

    model_config = ConfigDict(
        from_attributes=True
    )


class WorkdayApplication(BaseModel):
    id: Optional[int] = None
    workday_id: int
    application_id: int
    time_seconds: int


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

    def __eq__(self, other):
        if isinstance(other, ApplicationView):
            return self.name == other.name and self.is_productive == other.is_productive
        return NotImplemented

    def __repr__(self):
        return f"<Application(name='{self.app.name}', productivity={self.is_productive}, elapsed_time={self.elapsed_time})>"
