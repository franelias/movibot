import logging
import os

import requests
from paradas.paradas import dataParada
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, ConversationHandler

PARADA, DETALLES = range(2)
movi_url = os.getenv("MOVI_URL", default="")
logger = logging.getLogger(__name__)


def cuandoLlega(update: Update, context: CallbackContext):
    colectivos = requests.get(f"{movi_url}/lineas",
                              params={"nombre": "all"}).json()

    teclado_colectivos = []

    for colectivo in colectivos:
        context.user_data[colectivo["nombre"]] = colectivo
        teclado_colectivos.append([colectivo["nombre"]])

    markup = ReplyKeyboardMarkup(teclado_colectivos, one_time_keyboard=True)

    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Elegí una linea:", reply_markup=markup)

    return PARADA


def buscarParadas(update: Update, context: CallbackContext):
    nombre_colectivo = update.message.text

    context.user_data["colectivo_seleccionado"] = nombre_colectivo

    colectivo_data = context.user_data[nombre_colectivo]

    detalles_colectivo = requests.get(
        f'{movi_url}/linea/{colectivo_data["idEmpresa"]}/{colectivo_data["id"]}').json()

    teclado_paradas = []

    for parada in detalles_colectivo["paradas"]:
        context.user_data[parada["nombre"]] = parada
        teclado_paradas.append([parada["nombre"]])

    markup = ReplyKeyboardMarkup(teclado_paradas, one_time_keyboard=True)

    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Elegí una parada:", reply_markup=markup)

    return DETALLES


def colectivoEnParada(update: Update, context: CallbackContext):
    nombre_parada = update.message.text

    parada_data = context.user_data[nombre_parada]

    cuando_llega_parada = dataParada(
        parada_data["id"], context.user_data["colectivo_seleccionado"])

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=cuando_llega_parada, reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END
