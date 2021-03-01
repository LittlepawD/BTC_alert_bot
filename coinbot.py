import alerts as al
import multiprocessing as mp
import random
from telebot import types

import telebot, pickle, time


# TODO: Import token using env!
with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.alerts = al.load_alerts()
        # TODO make loading and saving this set possible in case of crash?
        # this is for saving message id used in process of setting new alert
        self.alert_setting_set = set()

    def notify_alert(self, alert: al.Alert, cur_price):
        message = f"BTC Alert! Price is now {cur_price} EUR, {alert.notify} your {alert.price} alert."
        self.send_message(alert.owner, message)


bot = CoinBot(T_KEY)
lock = mp.Lock()

@bot.message_handler(commands = ["start", "help"])
def handle_start_help(message):
    help_text = """
    This bot is designed to help you track Bitcoin price.
    Use /set_alert to set new alert.
    Use /alerts to see your active alerts.
    Use /remove_alert to remove specified alert.
    Use /help to display this message.
    """
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
    send_message = f"Alert for what price? The current price is {al.get_price()}"
    sent_msg = bot.send_message(message.chat.id, send_message, reply_markup=markup)
    bot.alert_setting_set.add(sent_msg.message_id)
    print(bot.alert_setting_set)
    # save sent message id to wait for the reply

    # continuation, put to following functions

@bot.message_handler(func= lambda message: message.reply_to_message.message_id in bot.alert_setting_set)
def set_alert_step2(message: telebot.types.Message):
    print("setting step 2")
    new_id = message.message_id + message.chat.id
    bot.alerts[new_id] = al.Alert(new_id, message.chat.id)
    try:
        first_word = message.text.split(" ")[0]
        bot.alerts[new_id].set_price(first_word)

        # save alerts with new addition and confirm.
        lock.acquire()
        print("\tNew " + str(bot.alerts[new_id]))
        al.save_alerts(bot.alerts)
        lock.release()
        bot.send_message(bot.alerts[new_id].owner, f"Alert set for {bot.alerts[new_id].price} EUR.")

    except ValueError as err:
        print(f"While setting new alert, following error was handled: \n{err}")
        markup = types.ForceReply()
        sent_msg = bot.reply_to(message, "Sorry, I can't set the price to that. I need you to send a positive number.", reply_markup = markup)
        bot.alert_setting_set.add(sent_msg.message_id)

    bot.alert_setting_set.remove(message.reply_to_message.message_id)

    # TODO step 3 where notify above or below is determined

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

    # After exit mainloop, quit:
    bot.stop_polling()
    print("Stopped polling")
    bot_thread.join()
 