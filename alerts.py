class Alert:
    def __init__(self, id, owner, price = None, notify = None) -> None:
        self.id = id
        self.owner = owner
        self.price = price
        self.notify = notify
        self.was_notified = False

    def __str__(self) -> str:
        return f"Alert {self.id}: Notify {self.notify} {self.price} EUR."

    def __repr__(self) -> str:
        return self.id

    