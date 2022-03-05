import logging
import os

import requests
from telegram import Update
from telegram.ext import CallbackContext

movi_url = os.getenv("MOVI_URL", default="")
logger = logging.getLogger(__name__)


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
