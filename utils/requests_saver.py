import _io
import datetime
import telegram as tg


def add_new_note(date: datetime.datetime, name: str, address: str, tg_id: str, tg_handle: str):
    note = date.strftime('%d.%m.%Y') + ' ' + \
           name + ' ' + \
           address + ' ' + \
           tg_id + ' ' + \
           tg_handle + '\n'

    with open('db/requests.txt', 'a') as file:
        file.write(note)


def save_request(user: tg.User, address):
    date = datetime.datetime.now()
    name = (user.first_name if not user.first_name is None else '') + ' ' + (
        user.last_name if not user.last_name is None else '')
    tg_id = str(user.id)
    tg_handle = user.username if not user.username is None else ''

    add_new_note(date, name, address, tg_id, tg_handle)


def get_file() -> bytes:
    file = open('db/requests.txt', 'rb')
    return file
