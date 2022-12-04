import telegram as tg

PAYMENT_PROVIDER_TOKEN = "401643678:TEST:aecbefae-7d3d-40c4-a303-242f37972270"
MAX_UNPAID = 100000000000000000

CADASTRAL_NUMBER = 0
CAPTCHA_INSERT = 1
RESULT = 2

ADDRESS_INSERT = 3

ADDRESS_CHOOSE = 4
INFO_INSERT = 5

SCHEUlE_INSERT = 6

CONSULT_CHOOSE = 7

SLOT_CHOOSE = 8
LINK_INSERT = 9

ID_WRITE = 10
TEXT_WRITE = 11

ADDRESS_SELECT = 12

ADMINS = [464192926]

MENU = ['Узнать КС по кадастровому номеру',
        'Узнать КС по адресу',
        'Как снизить кадастровую стоимость',
        'Записаться на консультацию по снижению КС']

MENU_MARKUP = tg.ReplyKeyboardMarkup(
    list(map(lambda x: [x], MENU[:-1])),
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню')
