import abc
import typing
import typing as tp

import telegram as tg
import telegram.ext as tg_ext

import constant
from bot import messages
import client

import utils.user
import utils.request
import utils.info

from constant import RESULT, CADASTRAL_NUMBER, CAPTCHA_INSERT

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
        await update.message.reply_text(self.messages.start())


class HelpHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(self.messages.help())


class CadastralStartHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text(self.messages.cadastral_start())
        return CADASTRAL_NUMBER


class CadastralNumberHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        context.user_data['cadastral_number'] = update.message.text
        sent_message = await context.bot.send_message(chat_id=update.message.chat_id,
                                                      text=self.messages.wait())
        session.get_captcha()
        print(context.user_data['cadastral_number'])
        await context.bot.editMessageText(chat_id=update.message.chat_id,
                                          message_id=sent_message.message_id,
                                          text=self.messages.captcha_insert())
        await update.message.reply_photo(photo=open('captcha.png', 'rb'))
        return CAPTCHA_INSERT


class CaptchaHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        sent_message = await context.bot.send_message(chat_id=update.message.chat_id,
                                                      text=self.messages.wait())
        captcha_decode = update.message.text
        session.check_captcha(captcha_decode)
        cadastral_number = context.user_data['cadastral_number']
        info = session.get_info(cadastral_number)
        await context.bot.editMessageText(chat_id=update.message.chat_id,
                                          message_id=sent_message.message_id,
                                          text=info)
        return tg_ext.ConversationHandler.END


class CancelHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        await update.message.reply_text(self.messages.cancel(),
                                        reply_markup=tg.ReplyKeyboardRemove())
        return tg_ext.ConversationHandler.END


class AddressHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        tg_id = update.message.from_user.id
        if not utils.user.check_paid(tg_id):
            await update.message.reply_text(self.messages.address_count_error())
            return tg_ext.ConversationHandler.END

        await update.message.reply_text(self.messages.address())
        return constant.ADDRESS_INSERT


class AddressGetHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        address = update.message.text
        tg_id = update.message.from_user.id
        utils.request.create_request(tg_id, address)
        await update.message.reply_text(self.messages.address_success())
        for admin_id in constant.ADMINS:
            await context.bot.send_message(chat_id=admin_id,
                                           text=f"Появился новый запрос:\n{address}")
        return tg_ext.ConversationHandler.END


class IdHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        print(update.message.chat_id, update.message.from_user.id)
        await update.message.reply_text(str(update.message.chat_id))


# /list
class ActualListHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> None:
        if update.message.from_user.id not in constant.ADMINS:
            return
        actual_list = utils.request.get_actual_list_str()
        await update.message.reply_text(actual_list)


# /process
class ProcessHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END

        actual_list_markup = utils.request.get_actual_list_markup()
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
        await update.message.reply_text("Адрес выбран. Введите найденную информацию.")
        return constant.INFO_INSERT


class InfoHandler(BaseHandler):
    async def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        chosen_address = context.user_data.get('chosen_address', '')
        info = update.message.text

        try:
            user_ids = utils.request.manage_requests(chosen_address, info)

            for uid in user_ids:
                await context.bot.send_message(chat_id=uid,
                                               text=f'Информация по адресу: "{chosen_address}"'
                                                    f'найдена.')

                await update.message.reply_text('Информация сохранена успешно.')
                return tg_ext.ConversationHandler.END
        except KeyError:
            await update.message.reply_text(
                'Произошла ошибка. Запросов с выбранным адресом не осталось.')
            return tg_ext.ConversationHandler.END


# /schedule
class ScheduleStartHandler(BaseHandler):
    def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.from_user.id not in constant.ADMINS:
            return tg_ext.ConversationHandler.END
        await update.message.reply_text(self.messages.schedule_start())
        return constant.SCHEUlE_INSERT


class ScheduleInsertHandler(BaseHandler):
    def handle(
            self, update: tg.Update, context: tg_ext.ContextTypes.DEFAULT_TYPE
    ) -> int:
        raw = update.message.text

        return tg_ext.ConversationHandler.END


def cadastral_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.CommandHandler("cadastral", CadastralStartHandler())],

        states={

            CADASTRAL_NUMBER: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      CadastralNumberHandler())],
            CAPTCHA_INSERT: [
                tg_ext.MessageHandler(tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND,
                                      CaptchaHandler())
            ]

        },

        fallbacks=[tg_ext.CommandHandler("cancel", CancelHandler())],

    )

    return conversation_handler


def address_conversation() -> tg_ext.ConversationHandler:
    conversation_handler = tg_ext.ConversationHandler(

        entry_points=[tg_ext.CommandHandler("address", AddressHandler())],

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


def setup_handlers(application: tg_ext.Application, created_session: client.SearchSession) -> None:
    global session
    session = created_session

    application.add_handler(tg_ext.CommandHandler('start', StartHandler()))
    application.add_handler(tg_ext.CommandHandler('help', HelpHandler()))

    application.add_handler(cadastral_conversation())
    application.add_handler(address_conversation())
    application.add_handler(process_handler())
    application.add_handler(tg_ext.CommandHandler('id', IdHandler()))
    application.add_handler(tg_ext.CommandHandler('list', ActualListHandler()))
    # application.add_handler(
    #     tg_ext.MessageHandler(
    #         tg_ext.filters.TEXT & ~tg_ext.filters.COMMAND, EchoHandler()
    #     )
    # )
