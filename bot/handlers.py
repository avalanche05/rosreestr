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

session = None
session: client.SearchSession


class BaseHandler(abc.ABC):
    def __init__(self) -> None:
        self.user: tp.Optional[tg.User] = None

    async def __call__(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        self.user = update.effective_user
        self.messages = messages.get_messages(self.user)
        return await self.handle(update, context)

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
        await update.message.reply_text(self.messages.start(), reply_markup=constant.MENU_MARKUP,
                                        parse_mode='markdown')


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
            info = session.get_info(cadastral_number)
            await update.message.reply_text("Получилось! Вот информация о Вашем объекте:")
            await update.message.reply_text(info, reply_markup=constant.MENU_MARKUP)
        except Exception:
            await update.message
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
        if not utils.user.check_paid(tg_id):
            await update.message.reply_text(self.messages.address_count_error(),
                                            reply_markup=constant.MENU_MARKUP)
            return tg_ext.ConversationHandler.END

        await update.message.reply_text(self.messages.address(),
                                        reply_markup=tg.ReplyKeyboardRemove(), parse_mode="html")
        return constant.ADDRESS_INSERT


class AddressGetHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        address = update.message.text
        tg_id = update.message.from_user.id
        utils.request.create_request(tg_id, address)
        await update.message.reply_text(self.messages.address_success(),
                                        reply_markup=constant.MENU_MARKUP)
        for admin_id in constant.ADMINS:
            await context.bot.send_message(chat_id=admin_id,
                                           text=f"Появился новый запрос:\n{address}")
        return tg_ext.ConversationHandler.END


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
                                               text=f'Информация по адресу: "{chosen_address}" \n'
                                                    f'{info}',
                                               reply_markup=constant.MENU_MARKUP)

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
        text = '/list - список необработанных запросов\n' \
               '/process - обработать запросы\n' \
               '/schedule - настроить расписание\n' \
               '/calendar - посмотреть своё расписание\n' \
               '/link - отправить ссылку на консультацию'
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

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

    )

    return conversation_handler


def address_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[
            tg_ext.MessageHandler(tg_ext.filters.Regex(f"^{constant.MENU[1]}$"), AddressHandler())],

        states={

            constant.ADDRESS_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      AddressGetHandler())]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

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

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

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

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

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

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

    )
    return conversation_handler


def low_cost_handler() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.MessageHandler(tg_ext.filters.Regex(f"^{constant.MENU[2]}$"),
                                            CadastralPriceHandler())],

        states={

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

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

    application.add_handler(tg_ext.CommandHandler('admin', AdminHandler()))
    application.add_handler(tg_ext.CommandHandler('id', IdHandler()))
    application.add_handler(tg_ext.CommandHandler('list', ActualListHandler()))
    application.add_handler(tg_ext.CommandHandler('calendar', CalendarHandler()))
    application.add_handler(tg_ext.PreCheckoutQueryHandler(PreCheckoutHandler()))
    application.add_handler(
        tg_ext.MessageHandler(tg_ext.filters.SUCCESSFUL_PAYMENT, SuccessPayHandler())
    )
    # application.add_handler(
    #     tg_ext.MessageHandler(
    #         tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND, EchoHandler()
    #     )
    # )
