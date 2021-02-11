from alerts import *
import multiprocessing as mp

import telebot, pickle, time


with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.alerts = load_alerts()


bot = CoinBot(T_KEY)


@bot.message_handler(commands = ["start", "help"])
def handle_start_help(message):
    help_text = "this is a help text"
    bot.reply_to(message, help_text)

@bot.message_handler(commands = ["alerts"])
def handle_alerts(message):
    bot.reply_to(message, "alerts")

@bot.message_handler(commands = ["set_alert"])
def set_alert(message):
    pass

@bot.message_handler(commands = ["remove_alert"])
def handle_remove_alert(message):
    pass


def bot_start():
    bot.polling()

if __name__=='__main__':
    # test alerts:
    alerts = {}
    alerts[14] = Alert(14, "danko", 1451, "yes")
    save_alerts(alerts)

    lock = mp.Lock()
    bot_thread = mp.Process(target=bot_start)
    bot_thread.start()
    print(bot.alerts)


    cont = True
    while cont:
        try:
            # Mainloop:
            alerts = load_alerts()
            check_alerts(alerts)
            print("checked")
            time.sleep(2)
            
        except KeyboardInterrupt:
            cont = False

    bot.stop_polling()
    print("Stopped polling")
    bot_thread.join()
 