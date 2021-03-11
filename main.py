import alerts as al
import markups

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
logging.basicConfig(filename="log.log", level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%d-%m-%y %H:%M:%S')

@bot.message_handler(commands = ["start", "help"])
def handle_start_help(message):
    help_text = """
    This bot is designed to help you track Bitcoin price. You get a notification once the Bitcoin price gets above or below the set alert.

    Use /set_alert to set new alert.
    Use /alerts to see your active alerts.
    Use /remove_alert to remove specified alert.
    Use /price to get current Bitcoin price.
    Use /help to display this message.
    """
    # Add autoremove feature - removes all already notified alerts
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
    user_alerts = [alert for alert in bot.alerts.values() if alert.owner == message.chat.id]
    markup = markups.create_remove_alert_markup(user_alerts)
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
    try:
        new_id = al.generate_new_id(message)
        price = al.convert_str_price_to_float(message.text)
        bot.alerts[new_id] = al.Alert(new_id, message.chat.id, price)
        logging.info(f"New alert {bot.alerts[new_id]}")

    except ValueError as err:
        logging.info(f"While setting new alert, following error was handled: \n{err}")
        bot.reply_price_setting_fail(message)
        return

    lock.acquire()
    al.save_alerts(bot.alerts)
    lock.release()
    bot.send_message(bot.alerts[new_id].owner, f"Alert set for {bot.alerts[new_id].price} EUR.")
    bot.reply_price_setting_success(message, new_id)
    # TODO add option to set one time / persistent alert

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
    logging.info(f"Updated {alert}: {option}.")
    bot.send_message(alert.owner, f"Saved. You will be notified {alert.notify} {alert.price} EUR.")
    bot.await_callback_set.remove(query.message.message_id)

    lock.acquire()
    al.save_alerts(bot.alerts)
    lock.release()

@bot.callback_query_handler(func = lambda query: query.message.message_id in bot.await_alert_remove_set)
def alert_remove_callback_handler(query: types.CallbackQuery):
    bot.answer_callback_query(query.id)
    remove_alert_id = int(query.data)
    removed_alert = bot.alerts.pop(remove_alert_id)
    logging.info(f"Removed alert {removed_alert}")
    bot.reply_alert_removed(removed_alert, query)

    lock.acquire()
    al.save_alerts(bot.alerts)
    lock.release()

@bot.message_handler(func = lambda message: "OwO" in message.text)
def easter_egg(message: types.Message):
    bot.reply_to(message, "_OwO what's this?_", parse_mode="MarkdownV2")
    logging.info(f"User {message.chat.id} OwOed.")

# Anwser all unhandled callback queries
@bot.callback_query_handler(lambda query: True)
def unhandled_queries_handler(query):
    bot.answer_callback_query(query.id)


def bot_start():
    try:
        bot.polling()
    except Exception as e:
        logging.error("Error occurred in bot thread, quitting bot subprocess.")
        bot.stop_polling()
        exit()

if __name__=='__main__':
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
                # FIXME this really needs to be a function
                if not alert.was_notified:
                    if alert.notify == "above":
                        if cur_price > alert.price:
                            bot.notify_alert(alert, cur_price)
                            save_flag = True
                    elif alert.notify == "below":
                        if cur_price < alert.price:
                            remove = bot.notify_alert(alert, cur_price)
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
            print("checked")

            if save_flag:
                lock.acquire()
                al.save_alerts(alerts)
                lock.release()
            
            if not bot_thread.is_alive():
                logging.error("Bot thread stopped.")
                cont = False

            time.sleep(10)
            
        except KeyboardInterrupt:
            logging.info("Exitting...")
            cont = False
        
        except Exception as e:
            logging.error("Exception occured in mainloop")
            logging.exception(e)

    # After exit mainloop, quit:
    bot.stop_polling()
    print("Stopped polling")
    bot_thread.join()
    logging.info("Program stopped successfully.")
 