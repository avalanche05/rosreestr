import requests
import object

# CONSTANTS
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://lk.rosreestr.ru/eservices/real-estate-objects-online',
    'Pragma': 'no-cache',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin'
}
GET_CAPTCHA_LINK = 'https://lk.rosreestr.ru/account-back/captcha.png'
CHECK_CAPTCHA_LINK = 'https://lk.rosreestr.ru/account-back/captcha/'
GET_INFO_LINK = 'https://lk.rosreestr.ru/account-back/on'
GET_LIST_BY_ADDRESS_LINK = 'https://lk.rosreestr.ru/account-back/address/search' # ?term=%D0%BA%D0%B0%D0%BD%D0%B0%D1%88+%D1%87%D0%B8%D1%81%D1%82%D1%8B%D0%B5+%D0%BF%D1%80%D1%83%D0%B4%D1%8B&objType=all'


class SearchSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = HEADERS
        self.session.verify = False

        self.captcha_decode = None
        self.is_captcha_correct = False

        requests.packages.urllib3.disable_warnings()

    def get_captcha(self) -> None:
        """
        Метод сохраняет каптчу в captcha.png
        :return: None
        """
        self.is_captcha_correct = False
        response = self.session.get(GET_CAPTCHA_LINK)
        with open('captcha.png', 'wb') as file:
            file.write(response.content)

    def check_captcha(self, captcha_decode: str) -> bool:
        """
        Метод проверяет что ответ на каптчу верный.
        :param captcha_decode: расшифровка каптчи
        :return: возвращает True, если ответ на каптчу верный, иначе False
        """
        response = self.session.get(CHECK_CAPTCHA_LINK + captcha_decode)

        if response.ok:
            self.is_captcha_correct = True
            self.captcha_decode = captcha_decode
            return True
        else:
            return False

    def get_info(self, cadastral_number: str) -> object.Object:
        if not self.is_captcha_correct:
            raise SyntaxError('Перед чем использовать этот метод пройдите каптчу.')

        body = {
            "filterType": "cadastral",
            "cadNumbers": [cadastral_number],
            "captcha": self.captcha_decode
        }

        response = self.session.post(GET_INFO_LINK, json=body)

        if not response.ok:
            raise ConnectionError('Кадастровый номер неправильный')
        print(response.json())
        obj = object.get_object(response.json())
        return obj

    def get_list_by(self, address: str) -> list:
        params = {
            'term': address,
            'objType': 'all'
        }
        response = self.session.get(GET_LIST_BY_ADDRESS_LINK, params=params)
        return response.json()

