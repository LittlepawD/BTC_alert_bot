from telebot import types
import telebot

def create_set_alert_markup(new_alert_id):
        markup = types.InlineKeyboardMarkup()
        bt_a1 = types.InlineKeyboardButton("Above", callback_data = "ao" + str(new_alert_id))
        bt_b1 = types.InlineKeyboardButton("Below", callback_data = "bo" + str(new_alert_id))
        bt_a2 = types.InlineKeyboardButton("Above - Persistent", callback_data = "ap" + str(new_alert_id))
        bt_b2 = types.InlineKeyboardButton("Below - Persistent", callback_data = "bp" + str(new_alert_id))
        markup.row(bt_a1, bt_b1)
        markup.row(bt_a2, bt_b2)
        return markup

def unpack_notify_option_data(query_data: telebot.types.CallbackQuery):
    when = query_data[0]
    peristent_option = query_data[1]
    if when == "a":
        when = "above"
    elif when == "b":
        when = "below"
    else:
        raise ValueError("Unexpected value at [0]")

    if peristent_option == "o":
        persistent = False
    elif peristent_option == "p":
        persistent = True
    else:
        raise ValueError("Unexpected value at [1]")
    return when, persistent

def create_remove_alert_markup(user_alerts):
    markup = types.InlineKeyboardMarkup()
    for alert in user_alerts:
        button = types.InlineKeyboardButton(text=alert.print_for_user(), callback_data=alert.id)
        markup.row(button)
    return markup