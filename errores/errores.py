import html
import json
import logging
import os
import traceback

from telegram import ParseMode, Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)
dev_chat_id = os.getenv("DEV_CHAT_ID", default="")


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Ocurrió un error:",
                 exc_info=context.error)

    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'Ocurrió un error al handlear una update:\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        # f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        # f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    context.bot.send_message(chat_id=dev_chat_id,
                             text=message, parse_mode=ParseMode.HTML)

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Ups! Ocurrió un error de nuestro lado, intentá nuevamente.")

# BUGS
# - Algunos mensajes de errores no se pueden mandar de lo largo que son
