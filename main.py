import logging
import os

from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from paradas.paradas import parada
from comoLlego.comoLlego import ORIGEN, DESTINO, CANTIDAD_CUADRAS, MAPA, buscarUbicacion, comoLlego, finalizarIngreso, ingresoCantidadCuadras, ingresoDestino, ingresoOrigen

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

    updater.dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('parada', parada))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()

# TODO:
# - Añadir error handler
