from copy import copy

import client
import data.requests
import data.users
import utils.user
from data import db_session
from data import requests


def create_request(tg_id: int, address: str) -> None:
    if not utils.user.check_paid(tg_id):
        raise PermissionError('Слишком много неоплаченных заказов')

    db_sess = db_session.create_session()

    request = requests.Request()
    request.tg_id = tg_id
    request.address = address

    db_sess.add(request)
    db_sess.commit()
    db_sess.close()

    utils.user.increment_unpaid(tg_id)


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
    """возвращает все незакрытые запросы с адресом address"""
    db_sess = db_session.create_session()
    result = []
    rqsts = db_sess.query(data.requests.Request).filter_by(address=address, is_managed=False).all()

    if requests is None:
        raise KeyError

    for r in rqsts:
        r: data.requests.Request
        r.result = info
        r.is_managed = True
        r.is_found = True

        result.append(copy(r))

    db_sess.commit()
    db_sess.close()
    return result


def get_user_requests_id(user_id):
    db_sess = db_session.create_session()
    rqsts = db_sess.query(data.requests.Request).filter_by(tg_id=user_id,
                                                           is_managed=True,
                                                           is_found=True,
                                                           is_paid=False).all()
    result = list(map(lambda x: x.id, rqsts))
    db_sess.close()
    return result


def close_request_get_info(request_id) -> str:
    db_sess = db_session.create_session()
    r = db_sess.query(data.requests.Request).filter_by(id=request_id).first()
    r.is_paid = True

    user = db_sess.query(data.users.User).filter_by(tg_id=r.tg_id).first()
    user.count_not_paid -= 1

    result = r.result

    db_sess.commit()
    db_sess.close()

    return result


def list_by_address(address: str, session: client.SearchSession) -> list:
    addresses = [(t['cadnum'], t['full_name']) for t in session.get_list_by(address)]
    return addresses
