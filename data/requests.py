import sqlalchemy
from data.db_session import SqlAlchemyBase


class Request(SqlAlchemyBase):
    __tablename__ = 'requests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    address = sqlalchemy.Column(sqlalchemy.String)
    tg_id = sqlalchemy.Column(sqlalchemy.String)

    is_managed = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_found = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_paid = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    result = sqlalchemy.Column(sqlalchemy.String, default='Информация не найдена.')
