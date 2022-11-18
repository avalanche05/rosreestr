import telegram as tg
import telegram.ext as tg_ext

import constant


async def create_info_payment(chat_id: str, context: tg_ext.ContextTypes.DEFAULT_TYPE, payload: str) -> None:
    """Создать форму оплаты запроса и отправить её пользователю с введённым chat_id"""
    title = "Оплата запроса"
    description = "Оплатите запрос, чтобы увидеть информацию по вашему адресу"
    # select a payload just for you to recognize its the donation from your bot
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    currency = "RUB"
    # price in dollars
    price = 100
    # price * 100 so as to include 2 decimal points
    prices = [tg.LabeledPrice("Оплата запроса", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    await context.bot.send_invoice(
        chat_id, title, description, payload, constant.PAYMENT_PROVIDER_TOKEN, currency, prices
    )
