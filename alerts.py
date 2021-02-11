import pickle
import requests as r

URL = "https://api.coinbase.com/v2/prices/spot?currency=EUR"
ALERTS_FILE = "alerts_dic.bin"

class Alert:
    def __init__(self, id, owner, price = None, notify = None) -> None:
        self.id = id
        self.owner = owner
        self.price = price
        self.notify = notify
        self.was_notified = False

    def __str__(self) -> str:
        return f"Alert {self.id}: Notify {self.owner} {self.notify} {self.price} EUR."

    def __repr__(self) -> str:
        return f"Alert {self.id} for {self.owner}"

def load_alerts(file = ALERTS_FILE) -> dict:
    with open(file, "rb") as f:
        alerts = pickle.load(f)
    return alerts

def save_alerts(alerts, file=ALERTS_FILE):
    with open(file, "wb") as f:
        pickle.dump(alerts, f)
    

def check_alerts(alerts):
    pass

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