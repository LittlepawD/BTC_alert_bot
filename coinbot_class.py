import alerts as al
import telebot
from telebot import types

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.alerts = al.load_alerts()
        # this is for saving message id used in process of setting new alert
        # TODO rename sensibly and move to separate class
        self.alert_setting_set = set()
        self.await_callback_set = set()

        # this is used for removing alerts
        self.await_alert_remove_set = set()

    def notify_alert(self, alert: al.Alert, cur_price):
        message = f"BTC Alert! Price is now {cur_price} EUR, {alert.notify} your {alert.price} alert."
        self.send_message(alert.owner, message)
        alert.was_notified = True

    def is_set_alert_step2_reply(self, message: types.Message):
        if hasattr(message.reply_to_message, "message_id"):
            if message.reply_to_message.message_id in self.alert_setting_set:
                return True
        return False

