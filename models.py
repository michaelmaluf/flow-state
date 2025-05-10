# models.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import datetime

# Create the base class
Base = declarative_base()


# Define models
class Application(Base):
    __tablename__ = 'application'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    is_productive = Column(Boolean, default=True)

    workday_stats = relationship("WorkdayStat", back_populates="application")

    def __repr__(self):
        return f"<Application(id={self.id}, name='{self.name}', productive={self.is_productive})>"


class Workday(Base):
    __tablename__ = 'workday'

    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.date.today, nullable=False, index=True)
    pomodoros_left = Column(Integer, default=3)
    productive_time_seconds = Column(Integer, default=0)
    non_productive_time_seconds = Column(Integer, default=0)

    workday_stats = relationship("WorkdayStat", back_populates="workday")
    sessions = relationship("Session", back_populates="workday")

    def __repr__(self):
        return f"<WorkDay(id={self.id}, date='{self.date}', productive={self.productive_time_seconds}s)>"


class WorkdayStat(Base):
    __tablename__ = 'workday_stat'

    id = Column(Integer, primary_key=True)
    workday_id = Column(Integer, ForeignKey('workday.id'), nullable=False)
    application_id = Column(Integer, ForeignKey('application.id'), nullable=False)
    time_seconds = Column(Integer, default=0)

    workday = relationship("Workday", back_populates="workday_stats")
    application = relationship("Application", back_populates="workday_stats")

    def __repr__(self):
        return f"<WorkdayStat(id={self.id}, app_id={self.application_id}, time={self.time_seconds}s)>"


class Session(Base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    workday_id = Column(Integer, ForeignKey('workday.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    interruption_count = Column(Integer, default=0)

    workday = relationship("Workday", back_populates="sessions")

    def __repr__(self):
        return f"<Session(id={self.id}, start='{self.start_time}', duration={self.duration_seconds}s)>"
