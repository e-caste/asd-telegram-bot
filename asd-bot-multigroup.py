"""
"asd"
    - cit. Anonimo il 6/9/69 d.C. alle 4.20pm
"""

import logging
from telegram import bot, chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from robbamia_multi import *
from datetime import datetime, timedelta
import time
import threading
from motivational_replies import *
import random
import os
import matplotlib.pyplot as plt
from subprocess import Popen
from multiprocessing import Process
from sys import stderr


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

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


def get_current_count_content(chat_id: str):
    with open(counts_dir + chat_id + cnt_file, 'r') as f:  # 'rw' is forbidden
        # 0 2019040809
        content = f.read().split(" ")
    asd_count = int(content[0])
    date = str(content[1])
    week_start = datetime(year=int(date[0:4]),
                          month=int(date[4:6]),
                          day=int(date[6:8]),
                          hour=int(date[8:10]))
    return asd_count, date, week_start

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    bot.send_message(chat_id=update.message.chat_id, text='Hi ' + update.message.from_user.first_name +
                                                          ', welcome to asd bot! I only count asds from a certain'
                                                          " group chat, so I'm pretty useless to you now :D")

def print_record(bot, update):
    chat_id = str(update.message.chat_id)
    record = -1
    with open(counts_dir + chat_id + db_file, 'r') as db:
        for line in db.readlines():
            tmp = int(line.split("\t")[0])
            if tmp > record:
                record = tmp
    bot.send_message(chat_id=chat_id, text="Il nostro record attuale di asd settimanali è di "
                                                            + str(record) + " asd. Asdate di più per batterlo!")

def print_average(bot, update):
    chat_id = str(update.message.chat_id)
    sum = 0
    cnt = 0
    with open(counts_dir + chat_id + db_file, 'r') as db:
        for line in db.readlines():
            tmp = int(line.split("\t")[0])
            if tmp != 0:
                sum += tmp
                cnt += 1
    avg = round(float(sum/cnt), 2)
    bot.send_message(chat_id=chat_id, text="La nostra media attuale di asd settimanali è di "
                                                          + str(avg) + " asd. Asdate di più per alzarla!")

def print_total(bot, update):
    chat_id = str(update.message.chat_id)
    sum = 0
    with open(counts_dir + chat_id + db_file, 'r') as db:
        for line in db.readlines():
            sum += int(line.split("\t")[0])
    current_count, *_ = get_current_count_content(chat_id)
    sum += current_count
    bot.send_message(chat_id=chat_id, text="Il nostro totale attuale di asd è di "
                                                          + str(sum) + " asd.")

def history_graph(bot, update, chat_id: str = ""):
    # the function has been invoked by a user, otherwise it has been invoked by notify()
    if chat_id == "":
        chat_id = str(update.message.chat_id)
    x = []
    y = []
    with open(counts_dir + chat_id + db_file, 'r') as db:
        for line in db.readlines()[2:]:  # skips first 2 lines which only contain a 0
            # starting date
            x.append(str(line.split("- ")[1].split(" ")[0]))
            # number of asds
            y.append(int(line.split("\t")[0]))

    plt.plot(x, y)
    plt.xticks(x, rotation=90)
    plt.tick_params(axis='x', which='major', labelsize=8)
    plt.tight_layout()
    path_to_graph = counts_dir + chat_id + graph_file
    if os.path.exists(path_to_graph):
        Popen(["rm", path_to_graph])
    plt.savefig(path_to_graph, dpi=300, bbox_inches='tight')

    bot.send_photo(chat_id=chat_id, photo=open(path_to_graph, 'rb'))


def asd_counter(bot, update):
    """
    this function increases the asd_count and writes it to disk
    when a new message on the filtered group contains at least 1 "asd"
    """
    if update.message.chat.type == chat.Chat.SUPERGROUP or \
            update.message.chat.type == chat.Chat.GROUP:
        print(str(datetime.now()) + " " + update.message.chat.title + " " + str(update.message.chat_id))

        chat_id = str(update.message.chat_id)  # originally an int

        # if the group is not yet in the database:
        # add it
        # and make the count
        # and database files
        # and launch the corresponding notifier
        add_group = False
        with open(group_db, 'r') as g_db:
            if chat_id not in g_db.read():
                add_group = True
        if add_group:
            with open(group_db, 'a') as g_db:
                g_db.write(chat_id + " 1\n")  # automatically set weekly to True
            with open(counts_dir + chat_id + cnt_file, 'a') as cnt:
                cnt.write("0 "
                          + str(datetime.today().year).zfill(4)
                          + str(datetime.today().month).zfill(2)
                          + str(datetime.today().day).zfill(2)
                          + "09"  # to receive notifications at 9a.m.
                          )
            with open(counts_dir + chat_id + db_file, 'a') as db:
                db.write("0\n0\n")  # at least 2 entries needed
            global notifiers_manager
            notifiers_manager.restart_notifiers()
            print("New group added to the database: " + chat_id)

        # text and caption are mutually exclusive so at least one is None
        text = update.message.text
        caption = update.message.caption
        if text is not None:
            asd_increment = text.lower().count("asd")
        elif caption is not None:
            asd_increment = caption.lower().count("asd")
        else:
            asd_increment = 0

        if asd_increment > 0:
            try:
                asd_count, date, week_start = get_current_count_content(chat_id)
                print(asd_count, date)
                with open(counts_dir + chat_id + cnt_file, 'w') as f:
                    asd_count += asd_increment
                    f.write(str(asd_count)
                            + " "
                            + date)
                print("asd counter increased to " + str(asd_count))

            except Exception as e:
                bot.send_message(chat_id=castes_chat_id, text="asd_counter_bot si è sminchiato perché:\n" + str(e))
                print(e, file=stderr)

def notify(bot, weekly: bool, chat_id: str):
    """
    this function is called at the launch of the script in the main function as a separate thread
    this function is NOT to be called by a Message or Command Handler
    we use time.sleep() with the number of seconds until the date found in current_count.txt
    + timedelta(days=7) - datetime.now()
    then notify group with a random phrase based on asd increase or decrease
    """
    while True:
        try:
            *_, start = get_current_count_content(chat_id)
            if weekly:
                td = timedelta(days=7)
                time_to_sleep = int((start + td - datetime.now()).total_seconds())
                print(chat_id + " " + str(time_to_sleep) + " weekly")
            else:  # monthly
                td = timedelta(days=30)
                time_to_sleep = int((start + td - datetime.now()).total_seconds())
                print(chat_id + " " + str(time_to_sleep) + " monthly")

            time.sleep(time_to_sleep)
            # time.sleep(5)
            # UPDATE asd_count VARIABLE AFTER SLEEPING
            asd_count, *_ = get_current_count_content(chat_id)
            # UPDATE DATABASE - append weekly result
            with open(counts_dir + chat_id + db_file, 'a') as db:
                db.write("\n" + str(asd_count)
                         + "\t"
                         + str(start)
                         + " - "
                         + str(start + td))
            start += td
            # UPDATE CURRENT COUNTER - overwrite and reset to 0
            with open(counts_dir + chat_id + cnt_file, 'w') as f:
                f.write("0 "
                        + str(start.year).zfill(4)
                        + str(start.month).zfill(2)
                        + str(start.day).zfill(2)
                        + str(start.hour).zfill(2))
            # READ 2 LATEST RESULTS FROM DATABASE
            with open(counts_dir + chat_id + db_file, 'r') as db:
                past_period_asd_count = asd_count
                _period_before_that_asd_count = int(db.readlines()[-2].split("\t")[0])

            if weekly:
                stats = "\n\nQuesta settimana abbiamo totalizzato " + str(past_period_asd_count) + " asd"
            else:  # monthly
                stats = "\n\nQuesto mese abbiamo totalizzato " + str(past_period_asd_count) + " asd"
            diff = str(abs(past_period_asd_count - _period_before_that_asd_count))
            if past_period_asd_count == _period_before_that_asd_count:
                reply = random.choice(equals)
                end = ", proprio come la scorsa settimana!"
            elif past_period_asd_count > _period_before_that_asd_count:
                reply = random.choice(ismore)
                end = ", ossia " + str(diff) + " asd in più rispetto alla scorsa settimana!"
            else: # past_week_asd_count < _week_before_that_asd_count:
                reply = random.choice(isless)
                end = ", ossia " + str(diff) + " asd in meno rispetto alla scorsa settimana. D'oh!"
            bot.send_message(chat_id=chat_id, text=reply+stats+end)
            history_graph(bot, None, chat_id)

        except Exception as e:
            bot.send_message(chat_id=castes_chat_id, text="asd_counter_bot si è sminchiato perché:\n" + str(e))
            print(e, file=stderr)

def change_notification_period(bot, update):
    keyboard = [
        [InlineKeyboardButton("⏱ every week", callback_data='weekly')],
        [InlineKeyboardButton("📆 every month", callback_data='monthly')],
        [InlineKeyboardButton("❌ close", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('How frequently do you wish to receive a stats notification for this group?',
                                             reply_markup=reply_markup)

def button(bot, update):
    chat_id = str(update.callback_query.message.chat_id)
    query = update.callback_query
    reply = ""
    global notifiers_manager
    try:
        if query.data == 'weekly':
            change_needed = False
            with open(group_db, 'r') as g_db:
                for group in g_db.readlines():
                    if group.startswith(chat_id):
                        if group.endswith("0\n"):
                            change_needed = True
                        break
            if change_needed:
                with open(group_db, 'r') as g_db:
                    g_db_lines = g_db.readlines()
                with open(group_db, 'w') as g_db:
                    for line in g_db_lines:
                        if line.startswith(chat_id):
                            g_db.write(chat_id + " 1\n")
                        else:
                            g_db.write(line)

                notifiers_manager.restart_notifiers()
                reply = "Switched from monthly to weekly notifications!"
            else:
                reply = "The notifications are already on a weekly basis."

        elif query.data == 'monthly':
            change_needed = False
            with open(group_db, 'r') as g_db:
                for group in g_db.readlines():
                    if group.startswith(chat_id):
                        if group.endswith("1\n"):
                            change_needed = True
                        break
            if change_needed:
                with open(group_db, 'r') as g_db:
                    g_db_lines = g_db.readlines()
                with open(group_db, 'w') as g_db:
                    for line in g_db_lines:
                        if line.startswith(chat_id):
                            g_db.write(chat_id + " 0\n")
                        else:
                            g_db.write(line)

                notifiers_manager.restart_notifiers()
                reply = "Switched from weekly to monthly notifications!"
            else:
                reply = "The notifications are already on a monthly basis."

        elif query.data == 'close':
            reply = "Closed."

        query.edit_message_text(text=reply)

    except Exception as e:
        query.edit_message_text(text=e)
        print(e, file=stderr)

def help(bot, update):
    """Send a message when the command /help is issued."""
    bot.send_message(chat_id=update.message.chat_id, text='https://youtu.be/cueulBxn1Fw')


def error(bot, update):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', bot, update.error)

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("changenotificationperiod", change_notification_period))
    dp.add_handler(CommandHandler("record", print_record))
    dp.add_handler(CommandHandler("average", print_average))
    dp.add_handler(CommandHandler("total", print_total))
    dp.add_handler(CommandHandler("graph", history_graph))
    dp.add_handler(CommandHandler("help", help))
    # for every message
    dp.add_handler(MessageHandler((Filters.text | Filters.photo | Filters.video | Filters.document) & Filters.group,
                                  asd_counter))
    # inline messages handler
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()


    # all the notifiers are its daemonic processes -> by restarting the manager, every notifier is correctly restarted
    # e.g. monthly -> weekly switch or the asd-bot is added to a new group
    updater_process = Process(target=updater.idle)
    global notifiers_manager  # the only way to access it from the asd_counter() and button() functions
    notifiers_manager = NotifiersManager(bot.Bot(token))
    updater_process.start()
    updater_process.join()

    # t1 = threading.Thread(target=updater.idle)
    # t2 = threading.Thread(target=notify_manager(bot.Bot(token)))
    #
    # t1.start()
    # t2.start()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    os.chdir(rasPi_working_directory)
    main()
