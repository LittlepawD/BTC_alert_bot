import alerts as al
import multiprocessing as mp
import random
from telebot import types

import telebot, pickle, time


with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.alerts = al.load_alerts()

    def notify_alert(alert: al.Alert, cur_price):
        message = f"BTC Alert! Price is now {cur_price} EUR, {alert.notify} your {alert.price} alert."
        self.send_message(alert.owner, message)


bot = CoinBot(T_KEY)
lock = mp.Lock()


@bot.message_handler(commands = ["start", "help"])
def handle_start_help(message):
    help_text = "this is a help text"
    bot.reply_to(message, help_text)

@bot.message_handler(commands = ["alerts"])
def display_alerts(message):
    # reload alerts?
    user_alerts = [alert for alert in bot.alerts.values() if alert.owner == message.chat.id]
    if len(user_alerts) == 0:
        reply = "You have not set any alerts yet. You can do so with /set_alert."
    else:
        reply = "Your alerts:\n\n"
        for alert in user_alerts:
            reply += f"Notify {alert.notify} {alert.price} EUR\n"
    bot.reply_to(message, reply)

@bot.message_handler(commands = ["set_alert"])
def set_alert(message):
    markup = types.ForceReply()
    bot.send_message(message.chat.id, "Alert for what price?", reply_markup=markup)
    #TODO Figure out how to carry on with markup
    new_id = message.message_id + message.chat.id
    bot.alerts[new_id] = al.Alert(new_id, message.chat.id)
    lock.acquire()
    print("\tNew " + str(bot.alerts[new_id]))
    al.save_alerts(bot.alerts)
    lock.release()
    bot.send_message(bot.alerts[new_id].owner, f"Alert set on {bot.alerts[new_id].price} EUR.")

@bot.message_handler(commands = ["remove_alert"])
def handle_remove_alert(message):
    pass

@bot.message_handler(commands= ["price"])
def send_price(message):
    reply = f"Current price is {al.get_price()} EUR for BTC."
    bot.reply_to(message, reply)

def bot_start():
    bot.polling()

if __name__=='__main__':

    bot_thread = mp.Process(target=bot_start)
    bot_thread.start()
    print(bot.alerts)

    cont = True
    while cont:
        try:
            # Mainloop:
            lock.acquire()
            alerts = al.load_alerts()
            lock.release()

            cur_price = al.get_price()
            save_flag = False
            for alert in [alert for alert in alerts.values() if not alert.was_notified]:
                if alert.notify == "above":
                    if cur_price > alert.price:
                        bot.notify_alert(alert, cur_price)
                        save_flag = True
                elif alert.notify == "below":
                    if cur_price < alert.price:
                        bot.notify_alert(alert, cur_price)
                        save_flag = True
           
            if save_flag:
                lock.acquire()
                al.save_alerts(alerts)
                lock.release()

            print("checked")
            time.sleep(10)
            
        except KeyboardInterrupt:
            cont = False

    bot.stop_polling()
    print("Stopped polling")
    bot_thread.join()
 