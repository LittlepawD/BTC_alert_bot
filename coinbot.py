import alerts as al
import multiprocessing as mp
import logging
from telebot import types


import telebot, pickle, time


# TODO: Import token using env!
with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.alerts = al.load_alerts()
        # this is for saving message id used in process of setting new alert
        # TODO rename sensibly
        self.alert_setting_set = set()
        self.await_callback_set = set()

        # this is used for removing alerts
        self.await_alert_remove_set = set()

    def notify_alert(self, alert: al.Alert, cur_price):
        message = f"BTC Alert! Price is now {cur_price} EUR, {alert.notify} your {alert.price} alert."
        alert.was_notified = True
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

@bot.message_handler(commands = ["remove_alert"])
def handle_remove_alert(message: types.Message):
    # TODO implement alert removal
    markup = types.InlineKeyboardMarkup()
    bt_list = []
    for user_alert in [alert for alert in bot.alerts.values() if alert.owner == message.chat.id]:
        print(user_alert)
        bt_list.append(
            types.InlineKeyboardButton(text=user_alert.print_for_user(), callback_data=user_alert.id)
        )
    print(bt_list)
    markup.add(*bt_list)
    msg = bot.reply_to(message, "What alert do you want to remove?", reply_markup = markup)
    bot.await_alert_remove_set.add(msg.message_id)

@bot.message_handler(commands= ["price"])
def send_price(message):
    reply = f"Current price is {al.get_price()} EUR for BTC."
    bot.reply_to(message, reply)

@bot.message_handler(commands = ["set_alert"])
def set_alert(message):
    markup = types.ForceReply()
    send_message = f"Alert for what price? The current price is {al.get_price()}"
    sent_msg = bot.send_message(message.chat.id, send_message, reply_markup=markup)
    # save sent message id to wait for the reply
    bot.alert_setting_set.add(sent_msg.message_id)

# FIXME this causes an exception if message that isnt reply wasn't handled by previous handlers
@bot.message_handler(func= lambda message: message.reply_to_message.message_id in bot.alert_setting_set)
def set_alert_step2(message: telebot.types.Message):
    new_id = message.message_id + message.chat.id
    bot.alerts[new_id] = al.Alert(new_id, message.chat.id)
    try:
        first_word = message.text.split(" ")[0]
        bot.alerts[new_id].set_price(first_word)
        print("\tNew " + str(bot.alerts[new_id]))

        # save alerts with new addition and confirm.
        lock.acquire()
        al.save_alerts(bot.alerts)
        lock.release()
        bot.send_message(bot.alerts[new_id].owner, f"Alert set for {bot.alerts[new_id].price} EUR.")
        markup = types.InlineKeyboardMarkup()
        bt_a = types.InlineKeyboardButton("Above", callback_data = "a" + str(new_id))
        bt_b = types.InlineKeyboardButton("Below", callback_data = "b" + str(new_id))
        markup.row(bt_a, bt_b)
        msg = bot.send_message(bot.alerts[new_id].owner, "When do you want to be notified?", reply_markup=markup)
        bot.await_callback_set.add(msg.message_id)

    except ValueError as err:
        print(f"While setting new alert, following error was handled: \n{err}")
        markup = types.ForceReply()
        send_msg = "I can't set the alert to that price. I need you to send a positive number. Please try again"
        sent_msg = bot.reply_to(message, send_msg, reply_markup = markup)
        bot.alert_setting_set.add(sent_msg.message_id)

    bot.alert_setting_set.remove(message.reply_to_message.message_id)

# TODO anwser callbacks that dont pass handler too, so they dont have to timeout
@bot.callback_query_handler(func = lambda query: query.message.message_id in bot.await_callback_set)
def alert_callback_handler(query: types.CallbackQuery):
    print(query.message.message_id)
    option = query.data[0]
    alert_id = int(query.data[1:])
    bot.answer_callback_query(query.id)
    if option == "a":
        bot.alerts[alert_id].notify = "above"
    elif option == "b":
        bot.alerts[alert_id].notify = "below"
    else:
        logging.error("Got an unexpected anwser in alert_callback_handler: {option}")
        return
    # save alerts here
    lock.acquire()
    al.save_alerts(bot.alerts)
    lock.release()
    alert = bot.alerts[alert_id]
    print(f"Updated {alert}")
    bot.send_message(alert.owner, f"Saved. You will be notified {alert.notify} {alert.price} EUR.")

@bot.callback_query_handler(func = lambda query: query.message.message_id in bot.await_alert_remove_set)
def alert_remove_callback_handler(query: types.CallbackQuery):
    bot.answer_callback_query(query.id)

    if query.data in bot.alerts:
        # FIXME looks like this condition doesnt work ok
        removed = bot.alerts.pop(query)
        bot.send_message(removed.owner, f'Alert "{removed.print_for_user} was removed."')

        lock.acquire()
        al.save_alerts(bot.alerts)
        lock.release()
    

def bot_start():
    bot.polling()

if __name__=='__main__':
    # TODO update logger time format
    logging.basicConfig(filename="log.log", level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info("STARTED")

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
            for alert in alerts.values():
                if not alert.was_notified:
                    if alert.notify == "above":
                        if cur_price > alert.price:
                            bot.notify_alert(alert, cur_price)
                            save_flag = True
                    elif alert.notify == "below":
                        if cur_price < alert.price:
                            bot.notify_alert(alert, cur_price)
                            save_flag = True
                else:
                    if alert.notify == "above":
                        if cur_price < alert.price:
                            alert.was_notified = False
                            save_flag = True
                    elif alert.notify == "below":
                        if cur_price > alert.price:
                            alert.was_notified = False
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
 