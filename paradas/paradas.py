import logging
import os

import requests
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

BUSCAR_PARADA = range(1)
movi_url = os.getenv("MOVI_URL", default="")
logger = logging.getLogger(__name__)


def dataParada(numero_parada: int, nombre_colectivo: str = None):
    data = requests.get(f"{movi_url}/cuandollega", params={
        "parada": numero_parada}).json()

    logger.info(data)

    if "error" in data:
        return "Hubo un error al comunicarse con el servidor Movi."

    if not data:
        return "No hay servicios por la zona."

    if nombre_colectivo:
        data = list(filter(
            lambda colectivo: colectivo["linea"]["nombre"] == nombre_colectivo, data))

        if not data:
            return "No hay servicios por la zona."

    colectivos_text = f"Parada {numero_parada}\n"

    for colectivo in data:
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

    return colectivos_text


def parada(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Ingresá el número de parada:")

    return BUSCAR_PARADA


def buscarParada(update: Update, context: CallbackContext):
    numero_parada = update.message.text

    try:
        numero_parada = int(numero_parada)
    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Número de parada inválido.")

        context.user_data.clear()
        return ConversationHandler.END

    colectivos_mensaje = dataParada(numero_parada)

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=colectivos_mensaje)

    context.user_data.clear()
    return ConversationHandler.END
