import pickle
import requests as r

URL = "https://api.coinbase.com/v2/prices/spot?currency=EUR"
ALERTS_FILE = "alerts_dic.bin"

class Alert:
    def __init__(self, id, owner, price = None, notify = None, is_persistent = False) -> None:
        """ 
        Alert data structure. 

        Notify: Specifies when to notify the user. Options are 'above', 'below', 'on' 
        """
        self.id = id
        self.owner = owner
        self.price = price
        self.notify = notify
        self.is_persistent = is_persistent
        self.was_notified = False
    
    def print_for_user(self):
        if self.is_persistent:
            return f"Notify every time {self.notify} {self.price} EUR."
        else:
            return f"Notify {self.notify} {self.price} EUR."

    def __str__(self) -> str:
        if self.is_persistent:
            return f"Alert {self.id}: Notify {self.owner} every time {self.notify} {self.price} EUR."
        else:
            return f"Alert {self.id}: Notify {self.owner} {self.notify} {self.price} EUR."

    def __repr__(self) -> str:
        return f"Alert {self.id} for {self.owner}"

def generate_new_id(message):
        new_id = message.message_id + message.chat.id
        return new_id

def convert_str_price_to_float(price: str) -> float:
    price = price.split(" ")[0]
    if "," in price:
        price = price.replace(",", ".")
    try:
        price = float(price)
    except ValueError as err:
        raise ValueError("Price string cannot be converted to number")

    if  price <= 0:
        raise ValueError("Price cannot be negative or zero")
    if price > 4294967295:
        raise ValueError("Price is out of range")
    return round(price, 2)

def load_alerts(file = ALERTS_FILE) -> dict:
    with open(file, "rb") as f:
        alerts = pickle.load(f)
    return alerts

def save_alerts(alerts, file=ALERTS_FILE):
    with open(file, "wb") as f:
        pickle.dump(alerts, f)
    print("Alerts saved")
    

def check_alert(alert: Alert) -> tuple:
    cur_price = get_price()
    notify_flag = False
    un_notify = False
    if not alert.was_notified:
        if alert.notify == "above":
            if cur_price > alert.price:
                notify_flag = True
        elif alert.notify == "below":
            if cur_price < alert.price:
                notify_flag = True
    else:
        if alert.notify == "above":
            if cur_price < alert.price:
                un_notify = True
        elif alert.notify == "below":
            if cur_price > alert.price:
                un_notify = True
    return notify_flag, un_notify

def get_price():
    with r.get(URL) as resp:
        if resp.ok:
            dic = dict(resp.json())
            return float(dic["data"]["amount"])
        else: 
            raise ConnectionError("Could not connect to coinbase API.")

if __name__ == '__main__':
    """Launching this will set alerts file to empty dictionary!"""
    save_alerts({})
