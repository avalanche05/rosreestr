import constant
import data.slots
from data import db_session
from data import slots
from datetime import datetime, timedelta


def get_new_slot(date: datetime, tg_id: int) -> slots.Slot:
    slot = slots.Slot()
    slot.date = str(date)
    slot.tg_id = tg_id
    return slot


def create_slots(raw: str, tg_id: int) -> None:
    db_sess = db_session.create_session()

    for t in raw.strip().split('\n'):
        date, time_start, time_end = t.split()

        day, month, year = map(int, date.split())
        hour_start, minute_start = map(int, time_start.split())
        hour_end, minute_end = map(int, time_end.split())

        datetime_start = datetime(day=day, month=month, year=year, hour=hour_start,
                                  minute=minute_start)
        datetime_end = datetime(day=day, month=month, year=year, hour=hour_end, minute=minute_end)

        delta = timedelta(hours=1)

        current = datetime_start
        while current + delta <= datetime_end:
            db_sess.add(get_new_slot(current, tg_id))
            current = current + delta

    db_sess.commit()
    db_sess.close()


def get_free_slots() -> list:
    db_sess = db_session.create_session()
    slots = db_sess.query(data.slots.Slot).filter_by(i)
    result = []


    return result
