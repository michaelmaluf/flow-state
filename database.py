from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from models import Base, Application, Workday, WorkdayStat, Session


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(
            url=db_url,
            pool_pre_ping=True,
            echo=True,
        )
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    def get_or_create_application(self, app_name, is_productive=False):
        session = self.get_session()
        app = session.query(Application).filter_by(name=app_name).first()

        if not app:
            app = Application(name=app_name, is_productive=is_productive)
            session.add(app)
            session.commit()

        session.close()
        return app

    def get_or_create_workday(self, date=None):
        if not date:
            date = datetime.date.today()

        session = self.get_session()
        workday = session.query(Workday).filter_by(date=date).first()

        if not workday:
            workday = Workday(date=date)
            session.add(workday)
            session.commit()

        session.close()
        return workday

    def update_application_time(self, app_name, seconds, is_productive=None):
        """Update application time and workday totals"""
        session = self.get_session()

        app = session.query(Application).filter_by(name=app_name).first()
        if not app:
            app = Application(name=app_name)
            if is_productive is not None:
                app.is_productive = is_productive
            session.add(app)
            session.flush()

        if is_productive is None:
            is_productive = app.is_productive

        today = datetime.date.today()
        workday = session.query(Workday).filter_by(date=today).first()
        if not workday:
            workday = Workday(date=today)
            session.add(workday)
            session.flush()

        stat = session.query(WorkdayStat).filter_by(
            workday_id=workday.id,
            application_id=app.id
        ).first()

        if not stat:
            stat = WorkdayStat(
                workday_id=workday.id,
                application_id=app.id,
                time_seconds=0
            )
            session.add(stat)

        stat.time_seconds += seconds

        if is_productive:
            workday.productive_time_seconds += seconds
        else:
            workday.non_productive_time_seconds += seconds

        session.commit()
        session.close()

    def start_session(self, app_name=None):
        """Start a new work session"""
        session = self.get_session()
        workday = self.get_or_create_workday()

        app_id = None
        if app_name:
            app = self.get_or_create_application(app_name)
            app_id = app.id

        work_session = Session(
            workday_id=workday.id
        )

        session.add(work_session)
        session.commit()
        session_id = work_session.id
        session.close()

        return session_id

    def end_session(self, session_id, interruption_count=0):
        """End a work session"""
        session = self.get_session()
        work_session = session.query(Session).filter_by(id=session_id).first()

        if work_session and not work_session.end_time:
            work_session.end_time = datetime.datetime.now()
            work_session.interruption_count = interruption_count

            delta = work_session.end_time - work_session.start_time
            work_session.duration_seconds = int(delta.total_seconds())

            session.commit()

        session.close()

    def get_today_stats(self):
        session = self.get_session()
        workday = self.get_or_create_workday()

        result = {
            'productive_time': workday.productive_time_seconds,
            'non_productive_time': workday.non_productive_time_seconds,
            'pomodoros_left': workday.pomodoros_left,
            'total_time': workday.productive_time_seconds + workday.non_productive_time_seconds,
            'productivity_ratio': 0
        }

        if result['total_time'] > 0:
            result['productivity_ratio'] = workday.productive_time_seconds / result['total_time']

        session.close()
        return result