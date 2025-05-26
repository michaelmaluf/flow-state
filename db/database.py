import datetime
import os
import sys
from contextlib import contextmanager

from sqlalchemy import create_engine, text, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy.sql.operators import from_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Base, ApplicationModel, SessionModel, WorkdayModel, WorkdayApplicationModel
from domain.models import Workday, Application, Session, WorkdayApplication


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

    def save_workday_application(self, workday_application: WorkdayApplication) -> None:
        with self.session_scope() as session:
            stmt = insert(WorkdayApplicationModel).values(
                workday_id=workday_application.workday_id,
                application_id=workday_application.application_id,
                time_seconds=workday_application.time_seconds
            )

            stmt = stmt.on_conflict_do_update(
                constraint='uq_workday_application_fks',
                set_=dict(
                    time_seconds=WorkdayApplicationModel.time_seconds + workday_application.time_seconds
                )
            )

            session.execute(stmt)

    def bulk_save_workday_applications(self, workday_applications: list[WorkdayApplication]):
        with self.session_scope() as session:
            values = [
                {k: v for k, v in app.dict().items() if k not in ['id', 'application']}
                for app in workday_applications
            ]

            stmt = insert(WorkdayApplicationModel).values(values)
            update_stmt = stmt.on_conflict_do_update(
                index_elements=['workday_id', 'application_id'],
                set_=dict(
                    time_seconds=WorkdayApplicationModel.time_seconds + text('excluded.time_seconds')
                )
            )
            session.execute(update_stmt)

    def save_session(self, current_session: Session):
        today = datetime.date.today()
        with self.session_scope() as db_session:
            session = SessionModel(**Session.to_dict(current_session))
            workday = db_session.query(WorkdayModel).filter_by(date=today).first()
            session.workday = workday
            db_session.add(session)

    def get_todays_workday(self) -> Workday:
        today = datetime.date.today()
        with self.session_scope() as session:
            workday = session.query(WorkdayModel).filter_by(date=today).first()

            if not workday:
                workday = WorkdayModel(date=today)
                session.add(workday)
                session.flush()

            return Workday.from_orm(workday)

    def update_workday(self, workday: Workday) -> None:
        with self.session_scope() as session:
            workday_model = session.get(WorkdayModel, workday.id)
            workday_model.productive_time_seconds = workday.productive_time_seconds
            workday_model.non_productive_time_seconds = workday.non_productive_time_seconds
            workday_model.pomodoros_left = workday.pomodoros_left

    def activate_pomodoro(self, workday: Workday) -> bool:
        pass

    def get_all_workdays_from(self, date: datetime.date) -> list[Workday]:
        with self.session_scope() as session:
            workdays = (session.query(WorkdayModel)
                        .options(joinedload(WorkdayModel.workday_applications)
                                 .joinedload(WorkdayApplicationModel.application))
                        .filter(WorkdayModel.date > date)
                        .all())

            return [Workday.from_orm(workday) for workday in workdays]

    def get_workday_totals_from(self, date: datetime.date):
        with self.session_scope() as session:
            workday_totals = (session.query(
                func.coalesce(func.sum(WorkdayModel.productive_time_seconds), 0).label('total_productive'),
                func.coalesce(func.sum(WorkdayModel.non_productive_time_seconds), 0).label('total_non_productive'),
            )
                              .filter(WorkdayModel.date > date)
                              .first())

            return workday_totals.total_productive, workday_totals.total_non_productive

    def get_workday_application_totals_from(self, date: datetime.date):
        with self.session_scope() as session:
            app_breakdowns = (session.query(
                ApplicationModel.name,
                ApplicationModel.is_productive,
                func.sum(WorkdayApplicationModel.time_seconds).label('total_time')
            )
                              .join(WorkdayApplicationModel.application)
                              .join(WorkdayApplicationModel.workday)
                              .filter(WorkdayModel.date >= date)
                              .group_by(ApplicationModel.id, ApplicationModel.name, ApplicationModel.is_productive)
                              .order_by(func.sum(WorkdayApplicationModel.time_seconds).desc())
                              .all())

            return app_breakdowns
