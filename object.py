import datetime
from collections import defaultdict


class Object:
    def __init__(self):
        # Общая информация
        self.object_type = None
        self.status = None
        self.cadastral_number = None
        self.cadastral_date = None
        self.own_type = None
        # Характеристики объекта
        self.address = None
        self.area = None
        self.purpose = None
        self.floor = None
        # Сведения о кадастровой стоимости
        self.cadastral_cost = None
        self.determination_date = None
        self.registration_date = None
        # Сведения о правах и ограничениях (обременениях)
        self.rights = []
        self.encumbrances = []

        # Допы для участков
        self.permitted_use = None

        # Допы для зданий
        self.floor_cnt = None
        self.wall_material = None
        self.finish_build_year = None
        self.commissioning_year = None

        self.old_numbers = []

    def __str__(self) -> str:
        res = 'Получилось! Вот информация о Вашем объекте: \n\n'
        res += f'Вид объекта недвижимости: {self.object_type}\n'
        res += f'Кадастровый номер: {self.cadastral_number}\n'

        res += f'Адрес (местоположение): {self.address}\n'
        res += f'Площадь, кв.м: {self.area}\n\n'
        res += f'*Кадастровая стоимость (руб): {self.cadastral_cost}*\n'

        return res


def get_str_date(seconds: int) -> str:
    try:
        date = datetime.datetime.utcfromtimestamp(seconds // 1000)
        str_date = date.strftime('%d.%m.%Y')
    except Exception:
        return '-'
    return str_date


def get_object(raw: dict) -> Object:
    raw = defaultdict(str, raw)
    result = Object()

    # Тип объекта ---------------------------------------------------------------
    element = raw['elements'][0]
    obj_type = element['objType']
    obj_text = 'Неизвестно'
    if obj_type == '002001003000':
        obj_text = 'Помещение'
    elif obj_type == '002001002000':
        obj_text = 'Здание'
    elif obj_type == '002001001000':
        obj_text = 'Земельный участок'
    result.object_type = obj_text
    # Статус -------------------------------------------------------------------
    result.status = 'Актуально' if element['status'] == '1' else 'Неактуально'
    # Кадастровый номер --------------------------------------------------------
    result.cadastral_number = element['cadNumber']
    # Дата присвоения кадастрового номера --------------------------------------
    date_seconds = element['regDate']
    result.cadastral_date = get_str_date(date_seconds)
    # Форма собственности ------------------------------------------------------

    # Характеристики объекта

    # Адрес (местоположение) ---------------------------------------------------
    result.address = element['address']['readableAddress']
    # Площадь, кв.м
    result.area = element['area']
    # Назначение
    result.purpose = element['purpose']
    # Этаж
    result.floor = element['levelFloor']

    # Сведения о кадастровой стоимости

    # Кадастровая стоимость (руб) ----------------------------------------------
    result.cadastral_cost = element['cadCost']
    # Дата определения ---------------------------------------------------------
    date_seconds = element['cadCostDeterminationDate']
    result.determination_date = get_str_date(date_seconds)
    # Дата внесения ------------------------------------------------------------
    date_seconds = element['cadCostRegistrationDate']
    result.registration_date = get_str_date(date_seconds)

    # Сведения о правах и ограничениях (обременениях)

    # Вид, номер и дата государственной регистрации права -----------------------
    for right in element['rights']:
        text = ''
        if right['rightTypeDesc']:
            text = right['rightTypeDesc'] + '\n'
        if right['rightNumber']:
            text += right['rightNumber'] + '\n'
        if right['rightRegDate']:
            text += 'от ' + get_str_date(right['rightRegDate']) + '\n'
        result.rights.append(text)

    # Ограничение прав и обременение объекта недвижимости -----------------------
    for encumbrance in element['encumbrances']:
        text = ''
        if encumbrance['typeDesc']:
            text += encumbrance['typeDesc'] + '\n'
        if encumbrance['encumbranceNumber']:
            text += encumbrance['encumbranceNumber'] + '\n'
        if encumbrance['startDate']:
            text += 'от ' + get_str_date(encumbrance['startDate']) + '\n'
        result.encumbrances.append(text)

    # Вид разрешенного использования --------------------------------------------
    result.permitted_use = element['permittedUseByDoc']

    # Количество этажей ---------------------------------------------------------
    result.floor_cnt = element['floor']
    result.wall_material = element['oksWallMaterial']
    result.finish_build_year = element['oksYearBuild']
    result.commissioning_year = element['oksCommisioningYear']

    # Ранее присвоенные номера
    for t in element['oldNumbers']:
        result.old_numbers.append(f'{t["numType"]}: {t["numValue"]}\n')

    return result
