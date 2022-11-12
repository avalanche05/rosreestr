import constant
import data.users
from data import db_session
from data import users


def check_paid(tg_id: int):
    print(tg_id, 'CHECK PAID')
    db_sess = db_session.create_session()

    user = db_sess.query(users.User).filter_by(tg_id=tg_id).first()
    db_sess.close()
    return user.count_not_paid < constant.MAX_UNPAID


def increment_unpaid(tg_id: int):
    db_sess = db_session.create_session()

    user = db_sess.query(users.User).filter_by(tg_id=tg_id).first()
    user.count_not_paid += 1
    db_sess.commit()
    db_sess.close()


def register_user(tg_id: int):
    print(tg_id, 'CHECK REGISTER')
    db_sess = db_session.create_session()

    user = db_sess.query(data.users.User).filter_by(tg_id=tg_id).first()

    if user is None:
        user = data.users.User()
        user.tg_id = tg_id
        db_sess.add(user)
        db_sess.commit()
    db_sess.close()
