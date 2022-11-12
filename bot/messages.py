import abc

import telegram as tg
import telegram.ext as tg_ext


class BaseMessages(abc.ABC):
    @abc.abstractmethod
    def start(self) -> str:
        raise NotImplemented

    @abc.abstractmethod
    def help(self) -> str:
        raise NotImplemented

    @abc.abstractmethod
    def cadastral_start(self):
        raise NotImplemented

    @abc.abstractmethod
    def wait(self):
        raise NotImplemented

    @abc.abstractmethod
    def captcha_insert(self):
        raise NotImplemented

    @abc.abstractmethod
    def cancel(self):
        raise NotImplemented

    @abc.abstractmethod
    def address(self):
        raise NotImplemented

    @abc.abstractmethod
    def address_count_error(self):
        raise NotImplemented

    @abc.abstractmethod
    def address_success(self):
        raise NotImplemented

    @abc.abstractmethod
    def schedule_start(self):
        raise NotImplemented


class RegularUser(BaseMessages):
    def start(self) -> str:
        return 'Привет!'

    def help(self) -> str:
        return 'Вам нужно приобрести подписку'

    def cadastral_start(self) -> str:
        return 'Введите кадастровый номер:'

    def wait(self):
        return 'Идёт загрузка...'

    def captcha_insert(self):
        return 'Введите каптчу: '

    def cancel(self):
        return 'Действие отменено'

    def address(self):
        return 'Введите адрес объекта'

    def address_count_error(self):
        return 'Вы сделали слишком много запросов. ' \
               'Пожалуйста, оплатите предыдущие запросы прежде чем делать новые.'

    def address_success(self):
        return 'Мы передали Ваш запрос нашим специалистам,' \
               ' как только мы найдём информацию, сразу Вам сообщим.'

    def schedule_start(self):
        return 'Введите ваши свободные часы в формате:\n' \
               'дд.мм.гггг 00:00 11:00\n' \
               'дд.мм.гггг 00:00 11:00\n\n' \
               'Каждый временной промежуток на новой строке. ' \
               'Если вы хотите добавить 2 временных промежутка в один день, ' \
               'например 12 ноября с 8 утра до 12 дня и с 5 вечера до 8 вечера,' \
               ' то вы должны написать:\n' \
               '12.11.2022 8:00 12:00\n' \
               '12.11.2022 17:00 20:00\n\n' \
               'Обратите внимание:\n' \
               '- считается, что одна консультация длится час.\n' \
               '- считается, что во время окончания временного промежутка вы уже заняты' \
               '(например, если вы указали время с 8 утра до 12 дня' \
               ' записаться к вам на консультацию можно будет на 8, 9, 10 или 11 часов.)'


class PremiumUser(RegularUser):
    def start(self) -> str:
        return 'Здравствуйте!'

    def help(self) -> str:
        return 'Наш менеджер скоро свяжется с вами!'


def get_messages(user: tg.User) -> BaseMessages:
    if not user.is_premium:
        return PremiumUser()
    return RegularUser()
