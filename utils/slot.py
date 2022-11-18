import constant
import data.slots
from data import db_session
import data.slots
from datetime import datetime, timedelta


def get_clear_slot(slot: data.slots.Slot) -> data.slots.Slot:
    result = data.slots.Slot()

    result.id = slot.id
    result.date = slot.date
    result.tg_id = slot.tg_id
    result.is_booked = slot.is_booked
    result.is_expired = slot.is_expired
    result.link = slot.link
    result.is_paid = slot.is_paid
    result.is_sent = slot.is_sent

    return result


def get_new_slot(date: datetime) -> data.slots.Slot:
    slot = data.slots.Slot()
    slot.date = str(date)
    return slot


def create_slots(raw: str) -> None:
    db_sess = db_session.create_session()

    for t in raw.strip().split('\n'):
        date, time_start, time_end = t.split()

        day, month, year = map(int, date.split('.'))
        hour_start, minute_start = map(int, time_start.split(':'))
        hour_end, minute_end = map(int, time_end.split(':'))

        datetime_start = datetime(day=day, month=month, year=year, hour=hour_start,
                                  minute=minute_start)
        datetime_end = datetime(day=day, month=month, year=year, hour=hour_end, minute=minute_end)

        delta = timedelta(hours=1)

        current = datetime_start
        while current + delta <= datetime_end:
            db_sess.add(get_new_slot(current))
            current = current + delta

    db_sess.commit()
    db_sess.close()


def get_free_slots() -> list:
    db_sess = db_session.create_session()
    slots = db_sess.query(data.slots.Slot).filter_by(is_booked=False, is_expired=False).all()

    result = []
    for slot in slots:
        slot: data.slots.Slot

        if not slot.check_on_time():
            slot.is_expired = True
            continue

        result.append(get_clear_slot(slot))

    db_sess.commit()
    db_sess.close()

    return result


def get_free_slots_list() -> tuple:
    """
    Метод возвращает два списка:
    1) список со свободным временем начала консультации
    2) id слотов в той же последовательности, что и первый список
    :return: list, list
    """
    raw = get_free_slots()
    times = []
    slots_id = []

    for slot in raw:
        slot: data.slots.Slot

        times.append(slot.get_datetime().strftime('%d.%m.%Y в %H:%M'))
        slots_id.append(slot.id)

    return times, slots_id


def get_list_for_markup(times: list) -> list:
    return [[t] for t in times]


def book_slot(slot_id: int, tg_id: int):
    db_sess = db_session.create_session()
    slot = db_sess.query(data.slots.Slot).filter_by(id=slot_id).first()

    if slot.is_booked:
        raise PermissionError('Время уже забронировано')

    slot.is_booked = True
    slot.tg_id = tg_id

    db_sess.commit()
    db_sess.close()


def get_schedule() -> list:
    db_sess = db_session.create_session()
    slots = db_sess.query(data.slots.Slot).filter_by(is_expired=False).all()
    result = []
    for slot in slots:
        slot: data.slots.Slot

        if not slot.check_on_time():
            slot.is_expired = True
            continue

        result.append(get_clear_slot(slot))

    db_sess.commit()
    db_sess.close()

    return result


def get_schedule_str() -> str:
    slots = get_schedule()

    result = ''

    for slot in slots:
        slot: data.slots.Slot

        start_time = slot.get_datetime().strftime('%d.%m.%Y в %H:%M')
        is_booked = slot.is_booked

        result += '- ' + start_time

        if is_booked:
            result += ' записались'

        result += '\n'

    return result


def get_booked_slots() -> list:
    db_sess = db_session.create_session()
    slots = db_sess.query(data.slots.Slot).filter_by(is_booked=True, is_expired=False).all()

    result = []
    for slot in slots:
        slot: data.slots.Slot
        result.append(get_clear_slot(slot))

    db_sess.commit()
    db_sess.close()

    return result


def get_booked_slots_list() -> tuple:
    """
    Метод возвращает два списка:
    1) список с забронированным временем начала консультации
    2) id слотов в той же последовательности, что и первый список
    :return: list, list
    """
    raw = get_booked_slots()
    times = []
    slots_id = []

    for slot in raw:
        slot: data.slots.Slot

        date = slot.get_datetime().strftime('%d.%m.%Y в %H:%M')
        if slot.is_sent:
            date += ' [отправлено]'
        times.append(date)
        slots_id.append(slot.id)

    return times, slots_id


def send_link_get_slot(slot_id: int, link: str) -> data.slots.Slot:
    db_sess = db_session.create_session()
    slot = db_sess.query(data.slots.Slot).filter_by(id=slot_id).first()
    slot.link = link
    slot.is_sent = True
    res_slot = get_clear_slot(slot)
    db_sess.commit()
    db_sess.close()
    return res_slot
