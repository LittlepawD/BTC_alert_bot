import pickle, time
import requests as r
import coinbot
import multiprocessing as mp

# Features:

# Set alert - over / under set price
# Remove alert
# View your alerts


URL = "https://api.coinbase.com/v2/prices/spot?currency=EUR"

def get_price():
    with r.get(URL) as resp:
        if resp.ok:
            dic = dict(resp.json())
            return float(dic["data"]["amount"])
        else: 
            raise ConnectionError("Could not connect to API server.")

def load_alerts():
    pass
    # lock here
    # with open(coinbot.ALERTS_FILE, "rb"):
    #     pickle.load

def mainloop():
    print(get_price())
    time.sleep(2)
    
    # check alerts
    # TODO: Both bot and mainloop access alerts list. Make sure they do not conflict!

if __name__ == "__main__":
    lock = mp.Lock()
    bot_process = mp.Process(target = coinbot.start_bot, kwargs={"lock": lock})
    bot_process.start()

    cont = True
    while cont:
        try:
            mainloop()
        except KeyboardInterrupt:
            cont = False
    print("Mainloop exited")
    bot_process.terminate()
    print("Bot process terminated")
    