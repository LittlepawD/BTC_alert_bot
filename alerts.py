import pickle

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

def load_alerts(file = ALERTS_FILE):
    with open(file, "rb") as f:
        alerts = pickle.load(f)
    return alerts

def save_alerts(alerts, file=ALERTS_FILE):
    with open(file, "wb") as f:
        pickle.dump(alerts, f)
    

def check_alerts(alerts):
    pass

if __name__ == '__main__':
    save_alerts({})