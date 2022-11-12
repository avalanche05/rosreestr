import sqlalchemy
from data.db_session import SqlAlchemyBase


# Класс временно не используется.
class Info(SqlAlchemyBase):
    __tablename__ = 'info'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    request_id = sqlalchemy.Column(sqlalchemy.Integer)
    text = sqlalchemy.Column(sqlalchemy.String)
