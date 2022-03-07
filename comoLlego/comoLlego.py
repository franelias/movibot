import logging
import os

import requests
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, ConversationHandler

ORIGEN, DESTINO, CANTIDAD_CUADRAS, MAPA = range(4)
movi_url = os.getenv("MOVI_URL", default="")
logger = logging.getLogger(__name__)


def buscarCalle(calles: str):
    try:
        calles = requests.get(f"{movi_url}/geojson/ubicaciones",
                              params={"term": calles}).json()
    except:
        return None, None

    logger.info(calles)

    if not calles["features"]:
        return None, None

    features = dict()

    teclado_respuestas = [["/cancelar"]]

    for feature in calles["features"]:
        if feature["properties"]["subtipo"] != "CALLE":
            nombre = feature["properties"]["name"]

            teclado_respuestas.append([nombre])
            features[nombre] = feature

    markup = ReplyKeyboardMarkup(teclado_respuestas, one_time_keyboard=True)

    return markup, features


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

    try:
        calles = requests.get(
            f"{movi_url}/geojson/comollego", params=params).json()
    except:
        None, None, None

    rutas = calles["rutas"]
    colectivos_text = "Te podés tomar los siguientes colectivos:\n"

    intersecciones = set()

    paradas_coordenadas = {}

    for ruta in rutas:
        ruta_colectivo = list(filter(lambda feature: feature["properties"]
                                     ["modo_descripcion"] == "Colectivo", ruta["tramos"]["features"]))

        logger.info(ruta_colectivo)

        nombre_parada = ruta_colectivo[0]["properties"]["desde"]["properties"]["nombre"]

        paradas_coordenadas[nombre_parada] = ruta_colectivo[0]["properties"]["desde"]["coordinates"]

        colectivos_text += "• " + \
            ruta["denominacion"] + \
            f' en {nombre_parada}\n'

        intersecciones.add(
            ruta_colectivo[0]["properties"]["desde"]["properties"]["nombre"])

    reply_keyboard = [["/cancelar"]]

    for interseccion in intersecciones:
        reply_keyboard.append([interseccion])

    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    return colectivos_text, paradas_coordenadas, markup


def comoLlego(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Origen: ")

    return ORIGEN


def ingresoOrigen(update: Update, context: CallbackContext):
    origen_mensaje = update.message.text

    if "features" in context.user_data.keys():
        if origen_mensaje not in context.user_data["features"].keys():
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="No se encontró el lugar de origen. Intentá de nuevo:", reply_markup=ReplyKeyboardRemove())

            context.user_data.clear()

            return ORIGEN

        origen = context.user_data["features"][origen_mensaje]

    else:
        markup, features = buscarCalle(origen_mensaje)

        if not features:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="No se encontró el lugar de origen. Intentá de nuevo:", reply_markup=ReplyKeyboardRemove())

            return ORIGEN

        if len(features) > 1:
            context.user_data["features"] = features

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Elegí un origen de la lista:", reply_markup=markup)

            return ORIGEN
        else:
            origen = features[list(features.keys())[0]]

    logger.info(origen)

    try:
        coordenadas = requests.get(
            f'{movi_url}/coordenadaLatLon/{origen["geometry"]["coordinates"][0]}/{origen["geometry"]["coordinates"][1]}/').json()

    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Hubo un error al comunicarse con el servidor Movi.", reply_markup=ReplyKeyboardRemove())

        context.user_data.clear()
        return ConversationHandler.END

    context.user_data['origen'] = {
        "nombre": origen["properties"]["name"],
        "coordenadas": coordenadas
    }

    logger.info("Origen: %s", origen["properties"]["name"])

    update.message.reply_text("Destino: ", reply_markup=ReplyKeyboardRemove())

    return DESTINO


def ingresoDestino(update: Update, context: CallbackContext):
    destino_mensaje = update.message.text

    if "features_destino" in context.user_data.keys():
        if destino_mensaje not in context.user_data["features_destino"].keys():
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="No se encontró el lugar de destino. Intentá de nuevo:", reply_markup=ReplyKeyboardRemove())

            context.user_data.clear()

            return DESTINO

        destino = context.user_data["features_destino"][destino_mensaje]

    else:
        markup, features = buscarCalle(destino_mensaje)

        if not features:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="No se encontró el lugar de destino. Intentá de nuevo:", reply_markup=ReplyKeyboardRemove())

            return DESTINO

        if len(features) > 1:
            context.user_data["features_destino"] = features

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Elegí un destino de la lista:", reply_markup=markup)

            return DESTINO
        else:
            destino = features[list(features.keys())[0]]

    logger.info(destino)
    logger.info(destino["geometry"]["coordinates"])

    try:
        if len(destino["geometry"]["coordinates"]) > 1:
            coordenadas_destino = destino["geometry"]["coordinates"][0]
        else:
            coordenadas_destino = destino["geometry"]["coordinates"]

        coordenadas = requests.get(
            f'{movi_url}/coordenadaLatLon/{coordenadas_destino[0]}/{coordenadas_destino[1]}/').json()

    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Hubo un error al comunicarse con el servidor Movi.", reply_markup=ReplyKeyboardRemove())

        context.user_data.clear()
        return ConversationHandler.END

    context.user_data['destino'] = {
        "nombre": destino["properties"]["name"],
        "coordenadas": coordenadas
    }

    logger.info("Destino: %s", destino["properties"]["name"])

    update.message.reply_text(
        "Cantidad de cuadras a caminar: ", reply_markup=ReplyKeyboardRemove())

    return CANTIDAD_CUADRAS


def ingresoCantidadCuadras(update: Update, context: CallbackContext):
    cantidad_cuadras = update.message.text

    context.user_data['cantidad_cuadras'] = cantidad_cuadras

    colectivos_resultado, paradas_coordenadas, markup = buscarColectivos(
        update, context)

    if not colectivos_resultado or not paradas_coordenadas or not markup:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Hubo un error al comunicarse con el servidor Movi.", reply_markup=ReplyKeyboardRemove())

        context.user_data.clear()
        return ConversationHandler.END

    context.user_data['paradas_coordenadas'] = paradas_coordenadas

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=colectivos_resultado, reply_markup=markup)

    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Si querés ver la ubicación de una de las paradas, seleccionala en el menú.", reply_markup=markup)

    return MAPA


def buscarUbicacion(update: Update, context: CallbackContext):
    nombre_parada = update.message.text

    paradas_coordenadas = context.user_data['paradas_coordenadas'][nombre_parada]

    longitud = paradas_coordenadas[0]
    latitud = paradas_coordenadas[1]

    logger.info(f'latitud: {latitud} longitud: {longitud}')

    context.bot.sendLocation(
        chat_id=update.effective_chat.id, latitude=latitud, longitude=longitud, reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END


def finalizarIngreso(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Operación cancelada.", reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()

    return ConversationHandler.END
