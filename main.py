import logging
import os

from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from comoLlego.comoLlego import (CANTIDAD_CUADRAS, DESTINO, MAPA, ORIGEN,
                                 buscarUbicacion, comoLlego, finalizarIngreso,
                                 ingresoCantidadCuadras, ingresoDestino,
                                 ingresoOrigen)
from errores.errores import error_handler
from feedback.feedback import MANDAR, empezarFeedback, enviarFeedback
from paradas.paradas import parada

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

telegram_token = os.getenv("TELEGRAM_TOKEN", default="")


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Hola! Gracias por usar el bot de la Movi. Usa /parada o /comollego para empezar")


def main():
    updater = Updater(token=telegram_token, use_context=True)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('comollego', comoLlego)],
        states={
            ORIGEN: [MessageHandler(Filters.text & ~(Filters.command), ingresoOrigen)],
            DESTINO: [MessageHandler(Filters.text & ~(Filters.command), ingresoDestino)],
            CANTIDAD_CUADRAS: [MessageHandler(
                Filters.text & ~(Filters.command), ingresoCantidadCuadras)],
            MAPA: [MessageHandler(Filters.text & ~(
                Filters.command), buscarUbicacion)]
        },
        fallbacks=[CommandHandler('cancelar', finalizarIngreso)],
    )

    feedback_handler = ConversationHandler(
        entry_points=[CommandHandler('feedback', empezarFeedback)],
        states={
            MANDAR: [MessageHandler(Filters.text & ~(Filters.command), enviarFeedback)],
        },
        fallbacks=[CommandHandler('cancelar', finalizarIngreso)],
    )

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('parada', parada))
    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(feedback_handler)
    updater.dispatcher.add_error_handler(error_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
