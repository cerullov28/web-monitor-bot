from telegram import Bot
import os

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text="🚨 TEST TELEGRAM: se leggi questo, funziona")
print("Messaggio inviato")


