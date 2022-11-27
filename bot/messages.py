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

    @abc.abstractmethod
    def schedule_updated(self):
        raise NotImplemented

    @abc.abstractmethod
    def consult_start(self):
        raise NotImplemented

    @abc.abstractmethod
    def consult_success(self):
        raise NotImplemented

    @abc.abstractmethod
    def choose_slot(self):
        raise NotImplemented

    @abc.abstractmethod
    def link_sent_successful(self, text):
        raise NotImplemented


class RegularUser(BaseMessages):
    def start(self) -> str:
        return """Что могу для Вас сделать:
1️⃣ узнать кадастровую стоимость по кадастровому номеру (это я могу сам, поэтому *бесплатно*);
2️⃣ узнать кадастровую стоимость по адресу (пока что тоже *бесплатно*);
3️⃣ рассказать, как снизить кадастровую стоимость самостоятельно. 
"""

    def help(self) -> str:
        return 'Вам нужно приобрести подписку'

    def cadastral_start(self) -> str:
        return """Введите, пожалуйста, кадастровый номер объекта в формате
*АА:ВВ:CCCCСCC:КК*, где
- *АА* — кадастровый округ.
- *ВВ* — кадастровый район.
- *CCCCCCС* — кадастровый квартал состоит из 6 или 7 цифр.
- *КК* — номер объекта недвижимости."""

    def wait(self):
        return 'Идёт загрузка...'

    def captcha_insert(self):
        return 'Введите, пожалуйста, каптчу. Это не моя прихоть, это Росреестр требует🤷'

    def cancel(self):
        return 'Действие отменено'

    def address(self):
        return 'Введите адрес объекта'

    def address_count_error(self):
        return 'Вы сделали слишком много запросов. ' \
               'Пожалуйста, оплатите предыдущие запросы прежде чем делать новые.'

    def address_success(self):
        return """Я передал Ваш запрос нашим специалистам. Как только они найдут информацию, сразу Вам сообщу."""

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

    def schedule_updated(self):
        return 'Ваше расписание обновлено'

    def consult_start(self):
        return 'Выберите время, на которое Вы хотите записаться.'

    def consult_success(self):
        return 'Вы успешно записались на консультацию. Скоро с Вами свяжутся наши менеджеры.'

    def choose_slot(self):
        return 'В выпадающей клавиатуре представлено время, в которое записались клиенты.' \
               ' Чтобы отправить ссылку на видео-созвон нажмите на интересующее вас время ' \
               'и введите текст-приглашение с ссылкой(этот текст увидит клиент)'

    def link_sent_successful(self, text):
        return 'Пользователю успешно отправился текст:\n\n' + text


def get_messages(user: tg.User) -> BaseMessages:
    return RegularUser()
