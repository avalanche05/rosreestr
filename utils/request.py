import data.requests
from data import db_session
from data import requests
from utils import user


def create_request(tg_id: int, address: str) -> None:
    if not user.check_paid(tg_id):
        raise PermissionError('Слишком много неоплаченных заказов')

    db_sess = db_session.create_session()

    request = requests.Request()
    request.tg_id = tg_id
    request.address = address

    db_sess.add(request)
    db_sess.commit()
    db_sess.close()

    user.increment_unpaid(tg_id)


def get_actual_list_markup() -> list:
    return [[t] for t in get_actual_list()]


def get_actual_list_str() -> str:
    requests_list = get_actual_list()

    result = "\n".join(map(lambda x: f"- {x}", requests_list))

    if not result:
        result = 'Необработанных запросов нет.'
    return result


def get_actual_list() -> list:
    db_sess = db_session.create_session()
    result = list(map(lambda x: x.address,
                      db_sess.query(data.requests.Request).filter_by(is_managed=False).all()))
    db_sess.close()
    return result


def manage_requests(address: str, info: str) -> list:
    db_sess = db_session.create_session()
    user_ids = []
    rqsts = db_sess.query(data.requests.Request).filter_by(address=address, is_managed=False).all()

    if requests is None:
        raise KeyError

    for r in rqsts:
        r: data.requests.Request
        r.result = info
        r.is_managed = True
        r.is_found = True

        user_ids.append(r.tg_id)

    db_sess.commit()
    db_sess.close()
    return user_ids
