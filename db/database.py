import datetime
import os
import sys
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Base, ApplicationModel, SessionModel, WorkdayModel, WorkdayStatModel
from domain.models import Workday, WorkdayStat, Application, Session

class Database:
    def __init__(self, db_url):
        self.engine = create_engine(
            url=db_url,
            pool_pre_ping=True,
            echo=True,
        )
        self.create_tables()
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

    @contextmanager
    def session_scope(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_or_create_application(self, app_name, is_productive) -> Application:
        with self.session_scope() as session:
            app = session.query(ApplicationModel).filter_by(name=app_name, is_productive=is_productive).first()
            if not app:
                app = ApplicationModel(name=app_name, is_productive=is_productive)
                session.add(app)
                session.flush()
            return Application.from_orm(app)

    def create_application(self, app_name, is_productive=False) -> Application:
        with self.session_scope() as session:
            app = ApplicationModel(name=app_name, is_productive=is_productive)
            session.add(app)
            session.flush()
            return Application.from_orm(app)

    def get_application(self, app_name) -> Application:
        with self.session_scope() as session:
            app = session.query(ApplicationModel).filter_by(name=app_name).first()
            return Application.from_orm(app) if app else None

    def get_or_create_workday(self) -> Workday:
        date = datetime.date.today()

        with self.session_scope() as session:
            workday = session.query(WorkdayModel).filter_by(date=date).first()

            if not workday:
                workday = WorkdayModel(date=date)
                session.add(workday)
                session.flush()

            return Workday.from_orm(workday)

    def save_workday_stat(self, workday: Workday, application: Application, seconds_elapsed: int) -> None:
        with self.session_scope() as session:
            workday_stat = session.query(WorkdayStatModel).filter_by(workday_id=workday.id, application_id=application.id).first()

            if not workday_stat:
                workday_stat = WorkdayStatModel(workday_id=workday.id, application_id=application.id, time_seconds=seconds_elapsed)
                session.add(workday_stat)
            else:
                workday_stat.time_seconds += seconds_elapsed

    def save_session(self, current_session: Session):
        with self.session_scope() as db_session:
            session = SessionModel(**Session.to_dict(current_session))
            db_session.add(session)



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
