from multiprocessing import Process
from robbamia_multi import group_db, token
import time
from asd_bot_multigroup import notify
from telegram import bot

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class NotifiersManager(metaclass=Singleton):
    def __init__(self, bot):
        self.notifiers = []
        self.bot = bot
        self.init_notifiers()

    def init_notifiers(self):
        with open(group_db, 'r') as g_db:
            for group in g_db.readlines():
                chat_id = str(group.split(" ")[0])
                weekly = bool(int(group.split(" ")[1]))
                self.notifiers.append(Process(target=notify, args=(self.bot, weekly, chat_id), daemon=True))
        for notifier in self.notifiers:
            notifier.start()
        for notifier in self.notifiers:
            notifier.join()

    def restart_notifiers(self):
        for notifier in self.notifiers:
            notifier.terminate()
        time.sleep(0.5)
        self.init_notifiers()

notifiers_manager = NotifiersManager(bot.Bot(token))
