import os
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

MANDAR = range(1)

dev_chat_id = os.getenv("DEV_CHAT_ID", default="")


def empezarFeedback(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Gracias por usar el bot! Dejanos tus comentarios a continuación:")

    return MANDAR


def enviarFeedback(update: Update, context: CallbackContext):
    feedback = "Feedback:\n" + update.message.text

    context.bot.send_message(chat_id=dev_chat_id, text=feedback)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Gracias!")

    return ConversationHandler.END
