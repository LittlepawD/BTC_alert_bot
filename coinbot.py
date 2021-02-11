from alerts import Alert
import multiprocessing as mp

import telebot, pickle, time

ALERTS_FILE = "alerts_dic.bin"

with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)


def define_bot(lock):
    bot = CoinBot(T_KEY)

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

    return bot

def bot_start(bot):
    bot.polling()

def check_alerts():
    pass

if __name__=='__main__':
    lock = mp.Lock()
    this_bot = define_bot(lock)
    bot_thread = mp.Process(target=bot_start, args=(this_bot,))
    bot_thread.start()

    cont = True
    while cont:
        try:
            # Mainloop:
            check_alerts(alerts, bot)
            print("checked")
            time.sleep(2)
            
        except KeyboardInterrupt:
            cont = False

    bot.stop_polling()
    print("Stopped polling")
    bot_thread.join()
 