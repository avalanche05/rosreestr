import abc
import typing
import typing as tp
import telegram as tg
import telegram.ext as tg_ext

import constant
import data.requests
from bot import messages
import client

import utils.user
import utils.request
import utils.info
import utils.slot
import utils.payments
import utils.requests_saver

session = None
session: client.SearchSession

CHECK_SUBSCRIBE = "checksubscribe"


class BaseHandler(abc.ABC):
    def __init__(self) -> None:
        self.user: tp.Optional[tg.User] = None

    async def __call__(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = '@d_zhelnin'

        chanel = await context.bot.get_chat(chat_id)
        chanel: tg.Chat

        chat_member = await chanel.get_member(user_id=update.effective_user.id)

        if not isinstance(self, StartHandler) and chat_member.status == tg.ChatMember.LEFT:
            await self.subscribe_handle(update, context)
            return
        self.user = update.effective_user
        self.messages = messages.get_messages(self.user)
        return await self.handle(update, context)

    async def subscribe_handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        keyboard = [
            [
                tg.InlineKeyboardButton("Подписался", callback_data=CHECK_SUBSCRIBE)
            ]
        ]
        reply_markup = tg.InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="""Упс! Что-то пошло не так 🤷‍♂️ 
Подпишись, пожалуйста, на канал @d_zhelnin""",
                                       reply_markup=reply_markup)
        return tg_ext.ConversationHandler.END

    @abc.abstractmethod
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        raise NotImplemented


class StartHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        utils.user.register_user(update.message.from_user.id)
        name = update.message.from_user.first_name
        name = name if name else "Уважаемый"
        keyboard = [
            [
                tg.InlineKeyboardButton("Подписался", callback_data=CHECK_SUBSCRIBE)
            ]
        ]
        reply_markup = tg.InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(self.messages.start(name), reply_markup=reply_markup)


class HelpHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(self.messages.help(), reply_markup=constant.MENU_MARKUP)


class CadastralStartHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text(self.messages.cadastral_start(),
                                        reply_markup=tg.ReplyKeyboardRemove(), parse_mode='markdown')
        return constant.CADASTRAL_NUMBER


class CadastralNumberHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        context.user_data['cadastral_number'] = update.message.text
        sent_message = await context.bot.send_message(chat_id=update.message.chat_id,
                                                      text=self.messages.wait(),
                                                      reply_markup=tg.ReplyKeyboardRemove())
        session.get_captcha()
        print(context.user_data['cadastral_number'])
        await update.message.reply_text(self.messages.captcha_insert())
        await update.message.reply_photo(photo=open('captcha.png', 'rb'))
        return constant.CAPTCHA_INSERT


class CaptchaHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        sent_message = await context.bot.send_message(chat_id=update.message.chat_id,
                                                      text=self.messages.wait(),
                                                      reply_markup=constant.MENU_MARKUP)
        captcha_decode = update.message.text
        if not session.check_captcha(captcha_decode):
            await update.message.reply_text("Попробуйте ввести каптчу ещё раз: ")
            return constant.CAPTCHA_INSERT
        cadastral_number = context.user_data['cadastral_number']
        try:
            obj = session.get_info(cadastral_number)
            utils.requests_saver.save_request(update.message.from_user, obj.address)
            await update.message.reply_text(str(obj), reply_markup=constant.MENU_MARKUP, parse_mode='markdown')
        except Exception:
            await update.message.reply_text("Введённый кадастровый номер неверный. Попробуйте ещё раз.",
                                            reply_markup=constant.MENU_MARKUP)

        return tg_ext.ConversationHandler.END


class CancelHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text(self.messages.cancel(), reply_markup=constant.MENU_MARKUP)
        return tg_ext.ConversationHandler.END


class AddressHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        tg_id = update.message.from_user.id

        await update.message.reply_text(self.messages.address(),
                                        reply_markup=tg.ReplyKeyboardRemove(), parse_mode="html")
        return constant.ADDRESS_INSERT


class AddressGetHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        address = update.message.text
        # utils.requests_saver.save_request(update.message.from_user, address)

        valid_list = utils.request.list_by_address(address, session)

        if not valid_list:
            await update.message.reply_text('Введённый адрес не найден. Введите адрес заново.')
            return constant.ADDRESS_INSERT

        context.user_data['valid_list'] = valid_list[:9]
        count = len(valid_list[:9])
        markup = []
        for i in range(count):
            if i % 3 == 0:
                markup.append([])
            markup[-1].append(i + 1)

        test = "Вот что удалось найти," \
               "Выберите номер, рядом с которым указан Ваш адрес.\n\n"
        for i in range(len(valid_list[:9])):
            test += str(i + 1) + ". " + valid_list[i][1] + '\n'

        try:
            await update.message.reply_text(test, reply_markup=tg.ReplyKeyboardMarkup(
                markup,
                one_time_keyboard=True,
                resize_keyboard=True,
                input_field_placeholder='Выберите номер'))
        except Exception:
            await update.message.reply_text('Слишком общий запрос. Попробуйте уточнить поиск.',
                                            reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END

        return constant.ADDRESS_SELECT


class ChooseAddressHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chosen_address = update.message.text

        valid_list = context.user_data.get('valid_list', [])

        chosen_address_cadnum = -1

        if chosen_address.isdigit() and int(chosen_address) <= len(valid_list):
            chosen_address_cadnum = valid_list[int(chosen_address) - 1][0]
        else:
            await update.message.reply_text('Вы выбрали адрес не из списка, пожалуйста, попробуйте заново.',
                                            reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END

        context.user_data['cadastral_number'] = chosen_address_cadnum
        sent_message = await context.bot.send_message(chat_id=update.message.chat_id,
                                                      text=self.messages.wait(),
                                                      reply_markup=tg.ReplyKeyboardRemove())
        session.get_captcha()
        print(context.user_data['cadastral_number'])
        await update.message.reply_text(self.messages.captcha_insert())
        await update.message.reply_photo(photo=open('captcha.png', 'rb'))
        return constant.CAPTCHA_INSERT


class IdHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        print(update.message.chat_id, update.message.from_user.id)
        await update.message.reply_text(str(update.message.chat_id),
                                        reply_markup=constant.MENU_MARKUP)


# /list
class ActualListHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message.from_user.id not in constant.ADMINS:
            return
        actual_list = utils.request.get_actual_list_str()
        await update.message.reply_text(actual_list, reply_markup=constant.MENU_MARKUP)


# /process
class ProcessHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            print('PROCESS NOT ADMIN')
            return tg_ext.ConversationHandler.END

        actual_list_markup = utils.request.get_actual_list_markup()

        if not actual_list_markup:
            await update.message.reply_text("Необработанных запросов нет.",
                                            reply_markup=tg.ReplyKeyboardRemove())
            return tg_ext.ConversationHandler.END
        print('PROCESS:', actual_list_markup)
        await update.message.reply_text("Выберите адрес",
                                        reply_markup=tg.ReplyKeyboardMarkup(
                                            actual_list_markup,
                                            one_time_keyboard=True,
                                            input_field_placeholder='Введите адрес'))
        return constant.ADDRESS_CHOOSE


class AddressChooseHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chosen_address = update.message.text

        if chosen_address not in utils.request.get_actual_list():
            await update.message.reply_text(
                'Выбранного запроса не существует. Выберите адрес на выпадающей клавиатуре')
            return constant.ADDRESS_CHOOSE

        context.user_data['chosen_address'] = chosen_address
        await update.message.reply_text("Адрес выбран. Введите найденную информацию.",
                                        reply_markup=tg.ReplyKeyboardRemove())
        return constant.INFO_INSERT


class InfoHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chosen_address = context.user_data.get('chosen_address', '')
        info = update.message.text

        try:
            rqsts = utils.request.manage_requests(chosen_address, info)

            for r in rqsts:
                r: data.requests.Request
                await context.bot.send_message(chat_id=r.tg_id,
                                               text=f'Получилось! Мы нашли Ваш объект - {chosen_address}. \n'
                                                    f'*Кадастровая стоимость: {info}*',
                                               reply_markup=constant.MENU_MARKUP,
                                               parse_mode='markdown')

            await update.message.reply_text('Информация сохранена успешно.',
                                            reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END
        except KeyError:
            await update.message.reply_text(
                'Произошла ошибка. Запросов с выбранным адресом не осталось.',
                reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END


# /schedule
class ScheduleStartHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        await update.message.reply_text(self.messages.schedule_start(),
                                        reply_markup=tg.ReplyKeyboardRemove())
        return constant.SCHEUlE_INSERT


class ScheduleInsertHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        raw = update.message.text

        utils.slot.create_slots(raw)
        await update.message.reply_text(self.messages.schedule_updated(),
                                        reply_markup=constant.MENU_MARKUP)
        return tg_ext.ConversationHandler.END


# /consult
class ConsultStartHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        times, slot_ids = utils.slot.get_free_slots_list()
        markup = utils.slot.get_list_for_markup(times)
        context.user_data['times'] = times
        context.user_data['slot_ids'] = slot_ids

        if not times:
            await update.message.reply_text('Свободных дат нет. Пожалуйста, попробуйте позже.')
            return tg_ext.ConversationHandler.END

        await update.message.reply_text(self.messages.consult_start(),
                                        reply_markup=tg.ReplyKeyboardMarkup(
                                            markup,
                                            one_time_keyboard=True,
                                            input_field_placeholder='Введите время'))
        return constant.CONSULT_CHOOSE


class ConsultChooseHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chosen_time = update.message.text
        times = context.user_data.get('times', [])
        slot_ids = context.user_data.get('slot_ids', [])

        if chosen_time not in times:
            await update.message.reply_text(
                'Неверное время. Выберите время с помощью выпадающих кнопок',
                reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END

        slot_id = slot_ids[times.index(chosen_time)]

        try:
            utils.slot.book_slot(slot_id, update.message.from_user.id)

            for admin_id in constant.ADMINS:
                await context.bot.send_message(chat_id=admin_id,
                                               text=f"Записались на консультацию:\n{chosen_time}")

            await update.message.reply_text(self.messages.consult_success(),
                                            reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END
        except PermissionError:
            await update.message.reply_text(
                'Консультацию уже успели забронировать. Пожалуйста, выберите другое время.',
                reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END


class CalendarHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message.from_user.id not in constant.ADMINS:
            return
        text = utils.slot.get_schedule_str()
        if not text:
            text = 'Расписание пустое.'
        await update.message.reply_text(text, reply_markup=constant.MENU_MARKUP)


class ManageStartHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        times, slots_id = utils.slot.get_booked_slots_list()
        context.user_data['times'] = times
        context.user_data['slots_id'] = slots_id

        if not times:
            await update.message.reply_text('Записей нет.')
            return tg_ext.ConversationHandler.END

        markup = utils.slot.get_list_for_markup(times)
        await update.message.reply_text(self.messages.choose_slot(),
                                        reply_markup=tg.ReplyKeyboardMarkup(
                                            markup,
                                            one_time_keyboard=True,
                                            input_field_placeholder='Выберите время'))
        return constant.SLOT_CHOOSE


class SlotChooseHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chosen_slot = update.message.text
        times = context.user_data.get('times', [])
        slots_id = context.user_data.get('slots_id', [])

        if chosen_slot not in times:
            await update.message.reply_text('Время не найдено, '
                                            'для выбора времени пользуйтесь выпадающей клавиатурой')
            return tg_ext.ConversationHandler.END

        await update.message.reply_text('Время выбрано. Ввведите ссылку.')

        slot_id = slots_id[times.index(chosen_slot)]

        context.user_data['slot_id'] = slot_id
        return constant.LINK_INSERT


class SlotLinkHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        link = update.message.text
        slot_id = int(context.user_data['slot_id'])
        slot = utils.slot.send_link_get_slot(slot_id, link)

        user_text = 'Информация по консультации которая пройдёт\n' + \
                    slot.get_datetime().strftime('%d.%m.%Y в %H:%M') + '\n\n' + \
                    link
        await context.bot.send_message(chat_id=slot.tg_id,
                                       text=user_text)

        await update.message.reply_text(self.messages.link_sent_successful(link))
        return tg_ext.ConversationHandler.END


class PreCheckoutHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.pre_checkout_query
        raw = query.invoice_payload.split('_')
        pay_type = raw[0]

        if pay_type == 'address':
            request_id = raw[1]
            if request_id not in map(str, utils.request.get_user_requests_id(
                    update.effective_user.id)):
                # answer False pre_checkout_query
                await query.answer(ok=False, error_message="Оплата не прошла. Попробуйте заново.")
            else:
                await query.answer(ok=True)
        elif pay_type == 'consult':
            pass
        else:
            await query.answer(ok=False, error_message="Внутренняя ошибка. Попробуйте заново.")


class SuccessPayHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        receipt = update.message.successful_payment
        raw = receipt.invoice_payload.split('_')
        pay_type = raw[0]

        if pay_type == "address":
            request_id = raw[1]
            await update.message.reply_text("Спасибо! Оплата прошла успешно."
                                            " Следующим сообщением высылаю вам информацию"
                                            " про ваш адрес.", reply_markup=constant.MENU_MARKUP)
            text = utils.request.close_request_get_info(request_id)
            await update.message.reply_text(text)
        elif pay_type == "consult":
            pass


class CadastralPriceHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text(
            text="<a href='https://t.me/d_zhelnin/62'>Гайд как снизить кадастровую стоимость самостоятельно.</a>",
            parse_mode="html",
            reply_markup=constant.MENU_MARKUP)
        return tg_ext.ConversationHandler.END


class StartWriteHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        await update.message.reply_text('Введите id пользователя, которому от имени бота нужно отправить сообщение.')
        return constant.ID_WRITE


class IdWriteHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        user_id = update.message.text
        context.user_data['user_id'] = user_id
        await update.message.reply_text('Теперь введите текст, который нужно отправить пользователю.')
        return constant.TEXT_WRITE


class TextWriteHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        user_id = context.user_data['user_id']
        message = update.message.text

        await context.bot.send_message(chat_id=user_id, text='Сообщение от администратора:')
        await context.bot.send_message(chat_id=user_id, text=message)
        await update.message.reply_text('Сообщение успешно отправлено.')

        return tg_ext.ConversationHandler.END


class FileHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        file = utils.requests_saver.get_file()
        await update.message.reply_document(file)


class StartBulkSend(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        await update.message.reply_text('Введите текст который нужно отправить всем пользователям.')
        return constant.GET_BULK_TEXT


class GetBulkText(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        bulk_text = update.message.text
        context.user_data['bulk_text'] = bulk_text
        await update.message.reply_text(
            "Бот отправит по всем пользователям сообщение следующего содержания")
        await update.message.reply_text(bulk_text)
        await update.message.reply_text('Вы уверены что хотите разослать это сообщение по всем пользователям?',
                                        reply_markup=tg.ReplyKeyboardMarkup(
                                            [['да', 'нет']],
                                            one_time_keyboard=True,
                                            input_field_placeholder='выберите')
                                        )
        return constant.CHECK_SEND


class SendBulk(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        ans = update.message.text
        if ans.lower().strip() != 'да':
            await update.message.reply_text('Отправка отменена.', reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END

        await update.message.reply_text('Идет загрузка...')
        bulk_text = context.user_data['bulk_text']
        from utils.excel import get_all_user_ids
        all_ids = list(set(get_all_user_ids()))
        print(all_ids)
        await update.message.reply_text(f'Сообщения будут разосланы {len(all_ids)} пользователям')

        err_cnt = 0
        for user_id in all_ids:
            try:
                await context.bot.send_message(chat_id=user_id,
                                               text=bulk_text)
            except Exception as e:
                err_cnt += 1

        if err_cnt > 0:
            await update.message.reply_text(f'Не получилось отправить {err_cnt} пользователям')

        await update.message.reply_text('Сообщения отправлены!', reply_markup=constant.MENU_MARKUP)
        return tg_ext.ConversationHandler.END


class CheckSubscribeHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chat_id = '@d_zhelnin'

        chanel = await context.bot.get_chat(chat_id)
        chanel: tg.Chat

        chat_member = await chanel.get_member(user_id=update.effective_user.id)

        if chat_member.status != tg.ChatMember.LEFT:

            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="Спасибо! Теперь можно пользоваться ботом. Выбери функцию в меню.",
                reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END
        else:
            keyboard = [
                [
                    tg.InlineKeyboardButton("Подписался", callback_data=CHECK_SUBSCRIBE)
                ]
            ]
            reply_markup = tg.InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="""Упс! Что-то пошло не так 🤷‍♂️ 
Подпишись, пожалуйста, на канал @d_zhelnin""",
                parse_mode="markdown",
                reply_markup=reply_markup)
            return tg_ext.ConversationHandler.END


def link_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.CommandHandler("link", ManageStartHandler())],

        states={

            constant.SLOT_CHOOSE: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      SlotChooseHandler())],
            constant.LINK_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      SlotLinkHandler())
            ]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

    )

    return conversation_handler


class AdminHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message.from_user.id not in constant.ADMINS:
            return
        text = '/send - отправить сообщение по id\n' \
               '/file - скачать файл с запросами\n' \
               '/bulk - разослать сообщение по всем пользователям'
        await update.message.reply_text(text)


def cadastral_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[
            tg_ext.MessageHandler(tg_ext.filters.Regex(f"^{constant.MENU[0]}$"),
                                  CadastralStartHandler())],

        states={

            constant.CADASTRAL_NUMBER: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      CadastralNumberHandler())],
            constant.CAPTCHA_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      CaptchaHandler())
            ]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )

    return conversation_handler


def bulk_send_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[
            tg_ext.CommandHandler("bulk", StartBulkSend())],

        states={

            constant.GET_BULK_TEXT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      GetBulkText())],
            constant.CHECK_SEND: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      SendBulk())
            ]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )

    return conversation_handler


def address_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[
            tg_ext.MessageHandler(tg_ext.filters.Regex(f"^{constant.MENU[1]}$"), AddressHandler())],

        states={

            constant.ADDRESS_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      AddressGetHandler())],
            constant.ADDRESS_SELECT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      ChooseAddressHandler())
            ],
            constant.CAPTCHA_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      CaptchaHandler())
            ]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )

    return conversation_handler


def process_handler() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.CommandHandler("process", ProcessHandler())],

        states={

            constant.ADDRESS_CHOOSE: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      AddressChooseHandler())],
            constant.INFO_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      InfoHandler())]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )
    return conversation_handler


def schedule_handler() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.CommandHandler("schedule", ScheduleStartHandler())],

        states={

            constant.SCHEUlE_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      ScheduleInsertHandler())]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )
    return conversation_handler


def consult_handler() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.MessageHandler(tg_ext.filters.Regex(f"^{constant.MENU[3]}$"),
                                            ConsultStartHandler())],

        states={

            constant.CONSULT_CHOOSE: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      ConsultChooseHandler())]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )
    return conversation_handler


def low_cost_handler() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.MessageHandler(tg_ext.filters.Regex(f"^{constant.MENU[2][:-len(' (гайд за подписку)')]}"),
                                            CadastralPriceHandler())],

        states={

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )
    return conversation_handler


def send_message_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.CommandHandler("send", StartWriteHandler())],

        states={

            constant.ID_WRITE: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      IdWriteHandler())],
            constant.TEXT_WRITE: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      TextWriteHandler())
            ]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler()), tg_ext.CommandHandler('start', StartHandler())],

    )

    return conversation_handler


def setup_handlers(application: tg_ext.Application, created_session: client.SearchSession) -> None:
    global session
    session = created_session

    application.add_handler(tg_ext.CommandHandler('start', StartHandler()))
    application.add_handler(tg_ext.CommandHandler('help', HelpHandler()))

    application.add_handler(cadastral_conversation())
    application.add_handler(address_conversation())
    application.add_handler(process_handler())
    application.add_handler(schedule_handler())
    application.add_handler(consult_handler())
    application.add_handler(link_conversation())
    application.add_handler(low_cost_handler())
    application.add_handler(send_message_conversation())
    application.add_handler(bulk_send_conversation())

    application.add_handler(tg_ext.CommandHandler('admin', AdminHandler()))
    application.add_handler(tg_ext.CommandHandler('id', IdHandler()))
    application.add_handler(tg_ext.CommandHandler('list', ActualListHandler()))
    application.add_handler(tg_ext.CommandHandler('calendar', CalendarHandler()))
    application.add_handler(tg_ext.PreCheckoutQueryHandler(PreCheckoutHandler()))
    application.add_handler(
        tg_ext.MessageHandler(tg_ext.filters.SUCCESSFUL_PAYMENT, SuccessPayHandler())
    )
    application.add_handler(tg_ext.CommandHandler('file', FileHandler()))

    application.add_handler(tg_ext.CallbackQueryHandler(CheckSubscribeHandler(), pattern="^" + CHECK_SUBSCRIBE + "$"))
    # application.add_handler(
    #     tg_ext.MessageHandler(
    #         tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND, EchoHandler()
    #     )
    # )
