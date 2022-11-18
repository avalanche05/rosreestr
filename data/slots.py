import datetime

import sqlalchemy
from data.db_session import SqlAlchemyBase


class Slot(SqlAlchemyBase):
    __tablename__ = 'slots'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    tg_id = sqlalchemy.Column(sqlalchemy.String)

    date = sqlalchemy.Column(sqlalchemy.String)

    is_booked = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_paid = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_expired = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_sent = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    link = sqlalchemy.Column(sqlalchemy.String, default='Ссылки ещё нет.')

    def get_datetime(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S")

    def check_on_time(self):
        return self.get_datetime() >= datetime.datetime.now()
