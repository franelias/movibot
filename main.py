from telegram import ReplyKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters
import requests
import logging
import os


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Hola! Gracias por usar el bot de la Movi. Usa /parada o /comollego para empezar")


def parada(update: Update, context: CallbackContext):
    mensaje_texo = ' '.join(update.message.text.split())

    try:
        numero_parada = mensaje_texo.split(" ")[1]
    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Parada no especificada.")
        return

    movi_request = requests.get(f"{movi_url}/cuandollega", params={
                                "parada": numero_parada})

    colectivos_json = movi_request.json()

    logger.info(msg=colectivos_json)

    if "error" in colectivos_json:
        if colectivos_json["error"] == "Ha ocurrido un error interno al ejecutar la operación":
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Error interno.")
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Parada inexistente.")

        return

    if not colectivos_json:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="No hay servicios por la zona.")
        return

    colectivos_text = ""

    for colectivo in colectivos_json:
        if colectivo["linea"]["nombre"] == "K" or colectivo["linea"]["nombre"] == "Q":
            colectivos_text += f'La {colectivo["linea"]["nombre"]} llega en:\n'
        else:
            colectivos_text += f'El {colectivo["linea"]["nombre"]} llega en:\n'

        for arribo in colectivo["arribos"]:
            colectivos_text += f'• {arribo["arriboEnMinutos"]} minutos, horario estimado {arribo["horaArribo"]}'

            if arribo["desvioHorario"] and arribo["desvioHorario"][0] == "+":
                colectivos_text += f', margen de error ±{arribo["desvioHorario"][1:]} \n'
            else:
                colectivos_text += "\n"

        colectivos_text += "\n"

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=colectivos_text)


ORIGEN, DESTINO, CANTIDAD_CUADRAS, SELECCIONAR_INTERSECCION = range(4)


def comoLlego(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Origen: ")

    return ORIGEN


def buscarCalle(calles: str):
    calles = requests.get(f"{movi_url}/geojson/ubicaciones",
                          params={"term": calles}).json()

    logger.info(calles)

    if not calles["features"]:
        return None

    if len(calles["features"]) == 1:
        if "altura" not in calles["features"][0]["properties"]:
            return None

        return calles["features"][0]

    reply_keyboard = []

    for calle in calles["features"]:
        nombre = calle["properties"]["name"]

        reply_keyboard.append([nombre])

    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    return markup


def comoLlegoOrigen(update: Update, context: CallbackContext):
    origen_mensaje = update.message.text

    origen = buscarCalle(origen_mensaje)

    if not origen:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Ingresá dirección y altura:", reply_markup=ReplyKeyboardRemove())

        return ORIGEN

    if type(origen) is ReplyKeyboardMarkup:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Seleccioná un origen:", reply_markup=origen)

        return ORIGEN

    coordenadas = requests.get(
        f'{movi_url}/coordenadaLatLon/{origen["geometry"]["coordinates"][0]}/{origen["geometry"]["coordinates"][1]}/',).json()

    context.user_data['origen'] = {
        "nombre": origen["properties"]["name"],
        "coordenadas": coordenadas
    }

    logger.info("Origen: %s", origen["properties"]["name"])

    update.message.reply_text("Destino: ", reply_markup=ReplyKeyboardRemove())

    return DESTINO


def comoLlegoDestino(update: Update, context: CallbackContext):
    destino_mensaje = update.message.text

    destino = buscarCalle(destino_mensaje)

    if not destino:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Ingresá dirección y altura:", reply_markup=ReplyKeyboardRemove())

        return DESTINO

    if type(destino) is ReplyKeyboardMarkup:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Seleccioná un destino:", reply_markup=destino)

        return DESTINO

    coordenadas = requests.get(
        f'{movi_url}/coordenadaLatLon/{destino["geometry"]["coordinates"][0]}/{destino["geometry"]["coordinates"][1]}/',).json()

    context.user_data['destino'] = {
        "nombre": destino["properties"]["name"],
        "coordenadas": coordenadas
    }

    logger.info("Destino: %s", destino["properties"]["name"])

    update.message.reply_text(
        "Cantidad de cuadras a caminar: ", reply_markup=ReplyKeyboardRemove())

    return CANTIDAD_CUADRAS


def cantidadCuadras(update: Update, context: CallbackContext):
    destino_mensaje = update.message.text
    context.user_data['cantidad_cuadras'] = destino_mensaje

    colectivos_resultado = buscarColectivos(update, context)

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=colectivos_resultado, reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END


def buscarColectivos(update: Update, context: CallbackContext):
    origen = context.user_data['origen']
    destino = context.user_data['destino']
    cantidad_cuadras = context.user_data['cantidad_cuadras']

    params = {
        "xOrigen": origen["coordenadas"]["longitud"],
        "yOrigen": origen["coordenadas"]["latitud"],
        "xDestino": destino["coordenadas"]["longitud"],
        "yDestino": destino["coordenadas"]["latitud"],
        "cantCuadras": cantidad_cuadras,
        "usarCoordenadasWGS84": "true"
    }

    calles = requests.get(
        f"{movi_url}/geojson/comollego", params=params).json()

    rutas = calles["rutas"]
    colectivos_text = "Te podés tomar los siguientes colectivos:\n"

    for ruta in rutas:
        ruta_colectivo = list(filter(lambda feature: feature["properties"]
                                     ["modo_descripcion"] == "Colectivo", ruta["tramos"]["features"]))

        colectivos_text += "• " + \
            ruta["denominacion"] + \
            f' en {ruta_colectivo[0]["properties"]["desde"]["properties"]["nombre"]}\n'

    return colectivos_text


def cancelar(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

telegram_token = os.getenv("TELEGRAM_TOKEN", default="")
movi_url = os.getenv("MOVI_URL", default="")

updater = Updater(token=telegram_token, use_context=True)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('comollego', comoLlego)],
    states={
        ORIGEN: [MessageHandler(Filters.text & ~(Filters.command), comoLlegoOrigen)],
        DESTINO: [MessageHandler(Filters.text & ~(Filters.command), comoLlegoDestino)],
        CANTIDAD_CUADRAS: [MessageHandler(
            Filters.text & ~(Filters.command), cantidadCuadras)]
    },
    fallbacks=[CommandHandler('cancelar', cancelar)],
)

updater.dispatcher.add_handler(conv_handler)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('parada', parada))

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
