from telebot import types

def create_set_alert_markup(new_alert_id):
        markup = types.InlineKeyboardMarkup()
        bt_a = types.InlineKeyboardButton("Above", callback_data = "a" + str(new_alert_id))
        bt_b = types.InlineKeyboardButton("Below", callback_data = "b" + str(new_alert_id))
        markup.row(bt_a, bt_b)
        return markup

def create_remove_alert_markup(user_alerts):
    markup = types.InlineKeyboardMarkup()
    for alert in user_alerts:
        button = types.InlineKeyboardButton(text=alert.print_for_user(), callback_data=alert.id)
        markup.row(button)
    return markup