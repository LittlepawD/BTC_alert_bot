from main import ALERTS_FILE
from alerts import Alert

import telebot, pickle

ALERTS_FILE = "alerts_dic.bin"

with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)

class CoinBot (telebot.TeleBot):
    def __init__(self, token, lock):
        super().__init__(token)
        self.lock = lock



def start_bot(lock):
    bot = CoinBot(T_KEY, lock)
 
    help_text = "this is a help text"

    @bot.message_handler(commands = ["start", "help"])
    def handle_start_help(message):
        bot.reply_to(message, help_text)

    @bot.message_handler(commands = ["alerts"])
    def handle_alerts(message):
        bot.reply_to(message, "alerts")

    @bot.message_handler(commands = ["set_alert"])
    def handle_set_alert(message):
        pass

    @bot.message_handler(commands = ["remove_alert"])
    def handle_remove_alert(message):
        pass
    
    bot.polling()