import datetime

from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ApplicationModel(Base):
    __tablename__ = 'application'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    is_productive = Column(Boolean, nullable=True)

    workday_applications = relationship("WorkdayApplicationModel", back_populates="application")

    __table_args__ = (
        UniqueConstraint('name', 'is_productive', name='uix_name_is_productive'),
    )

    def __repr__(self):
        return f"<ApplicationModel(id={self.id}, name='{self.name}', productive={self.is_productive})>"


class WorkdayModel(Base):
    __tablename__ = 'workday'

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.date.today, nullable=False, index=True)
    pomodoros_left = Column(Integer, default=3)

    workday_applications = relationship("WorkdayApplicationModel", back_populates="workday")
    sessions = relationship("SessionModel", back_populates="workday")

    def __repr__(self):
        return f"<WorkdayModel(id={self.id}, date='{self.date}')>"


class WorkdayApplicationModel(Base):
    __tablename__ = 'workday_application'

    id = Column(Integer, primary_key=True)
    workday_id = Column(Integer, ForeignKey('workday.id'), nullable=False)
    application_id = Column(Integer, ForeignKey('application.id'), nullable=False)
    time_seconds = Column(Integer, default=0)

    workday = relationship("WorkdayModel", back_populates="workday_applications")
    application = relationship("ApplicationModel", back_populates="workday_applications")

    __table_args__ = (
        UniqueConstraint('workday_id', 'application_id', name='uq_workday_application_fks'),
    )

    def __repr__(self):
        return f"<WorkdayApplicationModel(id={self.id}, app_id={self.application_id}, time={self.time_seconds}s)>"


class SessionModel(Base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    workday_id = Column(Integer, ForeignKey('workday.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    interruption_count = Column(Integer, default=0)

    workday = relationship("WorkdayModel", back_populates="sessions")

    def __repr__(self):
        return f"<SessionModel(id={self.id}, start='{self.start_time}', end={self.end_time})>"
