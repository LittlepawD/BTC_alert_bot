import alerts as al
import coinbot_class as cb
import multiprocessing as mp
import logging
from telebot import types

import pickle, time

# TODO: Import token using env!
with open("keys.bin", "rb") as f:       
    T_KEY, B_KEY, C_KEY = pickle.load(f)


bot = cb.CoinBot(T_KEY)
lock = mp.Lock()

# TODO simplify commands names

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
    markup = types.InlineKeyboardMarkup()
    user_alerts = [alert for alert in bot.alerts.values() if alert.owner == message.chat.id]
    for alert in user_alerts:
        button = types.InlineKeyboardButton(text=alert.print_for_user(), callback_data=alert.id)
        markup.row(button)
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

@bot.message_handler(func = bot.is_set_alert_step2_reply)
def set_alert_step2(message: types.Message):
    # FIXME Make this mess readable, break it down!
    new_id = message.message_id + message.chat.id
    try:
        first_word = message.text.split(" ")[0]
        price = al.convert_str_price_to_float(first_word)
        bot.alerts[new_id] = al.Alert(new_id, message.chat.id, price)
        print("\tNew " + str(bot.alerts[new_id]))

        lock.acquire()
        al.save_alerts(bot.alerts)
        lock.release()
        bot.send_message(bot.alerts[new_id].owner, f"Alert set for {bot.alerts[new_id].price} EUR.")

        # TODO move the following elsewhere
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

@bot.callback_query_handler(func = lambda query: query.message.message_id in bot.await_callback_set)
def alert_callback_handler(query: types.CallbackQuery):
    bot.answer_callback_query(query.id)
    option = query.data[0]
    alert_id = int(query.data[1:])
    if option == "a":
        bot.alerts[alert_id].notify = "above"
    elif option == "b":
        bot.alerts[alert_id].notify = "below"
    else:
        logging.error("Got an unexpected anwser in alert_callback_handler: {option}")
        return
    alert = bot.alerts[alert_id]
    print(f"Updated {alert}")
    bot.send_message(alert.owner, f"Saved. You will be notified {alert.notify} {alert.price} EUR.")
    lock.acquire()
    al.save_alerts(bot.alerts)
    lock.release()

@bot.callback_query_handler(func = lambda query: query.message.message_id in bot.await_alert_remove_set)
def alert_remove_callback_handler(query: types.CallbackQuery):
    bot.answer_callback_query(query.id)
    remove_alert_id = int(query.data)
    removed_alert = bot.alerts.pop(remove_alert_id)
    bot.send_message(removed_alert.owner, f'Alert "{removed_alert.print_for_user()} was removed."')
    # Important note: After this, the inline keyboard is still active and more alerts can be removed.
    # Consider deactivating it eventually?
    # Also, if already removed alert is clicked it results in an error, 
    # Also, tracking set can grow a lot. It is reset on restart tho.

    lock.acquire()
    al.save_alerts(bot.alerts)
    lock.release()

# Anwser all unhandled callback queries
@bot.callback_query_handler(lambda query: True)
def unhandled_queries_handler(query):
    bot.answer_callback_query(query.id)


def bot_start():
    bot.polling()

if __name__=='__main__':
    # TODO update logger time format
    logging.basicConfig(filename="log.log", level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info("STARTED")
    # TODO full exception logging

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
 