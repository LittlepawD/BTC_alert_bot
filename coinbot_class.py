import alerts as al
import markups
import telebot
from telebot import types

class CoinBot (telebot.TeleBot):
    def __init__(self, token):
        super().__init__(token)
        self.reload_alerts()
        # this is for saving message id used in process of setting new alert
        # TODO rename sensibly and move to separate class
        self.alert_setting_set = set()
        self.await_callback_set = set()

        # this is used for removing alerts
        self.await_alert_remove_set = set()
    
    def reload_alerts(self):
        self.alerts = al.load_alerts()

    def notify_alert(self, alert: al.Alert, cur_price):
        message = f"BTC Alert! Price is now {cur_price} EUR, {alert.notify} your {alert.price} alert."
        self.send_message(alert.owner, message)
        alert.was_notified = True
    
    def reply_price_setting_fail(self, original_message):
        markup = types.ForceReply()
        send_msg = "I can't set the alert to that price. I need you to send a positive number. Please try again"
        sent_msg = self.reply_to(original_message, send_msg, reply_markup = markup)
        self.alert_setting_set.remove(original_message.reply_to_message.message_id)
        self.alert_setting_set.add(sent_msg.message_id)
    
    def reply_price_setting_success(self, message, new_id):
        markup = markups.create_set_alert_markup(new_id)
        msg = self.send_message(self.alerts[new_id].owner, "When do you want to be notified?", reply_markup=markup)
        self.alert_setting_set.remove(message.reply_to_message.message_id)
        self.await_callback_set.add(msg.message_id)
    
    def reply_notify_setting_succes(self, alert, message):
        self.send_message(alert.owner, f"Saved. You will be notified {alert.notify} {alert.price} EUR.")
        self.await_callback_set.remove(message.message_id)
    
    def reply_alert_removed(self, alert, query):
        self.send_message(alert.owner, f'Alert "{alert.print_for_user()}" was removed.')
        self.await_alert_remove_set.remove(query.message.message_id)

    def is_set_alert_step2_reply(self, message: types.Message):
        if hasattr(message.reply_to_message, "message_id"):
            if message.reply_to_message.message_id in self.alert_setting_set:
                return True
        return False

