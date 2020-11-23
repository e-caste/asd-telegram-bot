"""
"asd"
    - cit. Anonimo il 6/9/69 d.C. alle 4.20pm
"""

import logging
from telegram import bot, chat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import datetime, timedelta
from time import sleep
from motivational_replies import *
import random
import os
import matplotlib.pyplot as plt
from subprocess import Popen
from sys import stderr
from multiprocessing import Process

# import Docker environment variables
token = os.environ["TOKEN"]
castes_chat_id = os.environ["CST_CID"]
counts_dir = os.environ["COUNTS_DIR"]
group_db = os.environ["GROUP_DB"]
db_file = os.environ["DB_FILE"]
cnt_file = os.environ["CNT_FILE"]
graph_file = os.environ["GRAPH_FILE"]

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def calculate_time_to_sleep(hour: int, minute: int = 0) -> int:
    """
    Calculate time to sleep to perform an action at a given hour and minute
    by e-caste
    """
    # hour is before given hour -> wait until today at given hour and minute
    if int(datetime.now().time().strftime('%k')) < hour:
        time_to_sleep = int(
            (datetime.today().replace(hour=hour, minute=minute, second=0)
             - datetime.now()).total_seconds())
    # hour is equal to given hour
    elif int(datetime.now().time().strftime('%k')) == hour:
        # minute is before given minute -> wait until today at given time
        if int(datetime.now().time().strftime('%M')) < minute:
            time_to_sleep = int(
                (datetime.today().replace(hour=hour, minute=minute, second=0)
                 - datetime.now()).total_seconds())
        # minute is after given minute -> wait until tomorrow at given time
        else:
            time_to_sleep = int(
                (datetime.today().replace(hour=hour, minute=minute, second=0) + timedelta(days=1)
                 - datetime.now()).total_seconds())
    # hour is after given hour -> wait until tomorrow at given time
    else:
        time_to_sleep = int(
            (datetime.today().replace(hour=hour, minute=minute, second=0) + timedelta(days=1)
             - datetime.now()).total_seconds())
    return time_to_sleep


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
    bot.send_message(chat_id=update.message.chat_id, text='Ciao ' + update.message.from_user.first_name +
                                                          ', benvenuto su asd bot! Conto solo gli asd dei gruppi'
                                                          ' dove sono presente, quindi a te ora non servo a nulla asd')


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
    if cnt == 0:
        avg = 0  # avoid dividing by 0
    else:
        avg = round(float(sum / cnt), 2)
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
    show_from_beginning = chat_id == ""
    if show_from_beginning:
        chat_id = str(update.message.chat_id)

    db_path = os.path.join(counts_dir, chat_id + db_file)
    if not os.path.exists(db_path):
        bot.send_message(chat_id=chat_id, text="Non ci sono statistiche salvate per questa chat. "
                                               "Prova in un gruppo dove sono presente! Asd")
    x = []
    y = []
    with open(db_path, 'r') as db:
        for line in db.readlines()[2:]:  # skips first 2 lines which only contain a 0
            try:
                # starting date
                x.append(str(line.split("- ")[1].split(" ")[0]))
                # number of asds
                y.append(int(line.split("\t")[0]))
            # skip groups that have wrongly formatted or no data
            except IndexError:
                return

    if not show_from_beginning:
        # only show the last half year progress when sending notification
        x = x[-26:]
        y = y[-26:]
        step = 1
    else:
        # only show 1 in step labels for readability
        step = int(len(x) / 50) + 1
    plt.plot(x, y)
    plt.xticks(range(0, len(x), step), x, rotation=90)
    plt.tick_params(axis='x', which='major', labelsize=8)
    plt.tight_layout()
    path_to_graph = os.path.join(counts_dir, chat_id + graph_file)
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
        logger.info(str(datetime.now()) + " " + update.message.chat.title + " " + str(update.message.chat_id))

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
                g_db.write(chat_id + "\n")
            with open(counts_dir + chat_id + cnt_file, 'a') as cnt:
                cnt.write("0 "
                          + str(datetime.today().year).zfill(4)
                          + str(datetime.today().month).zfill(2)
                          + str(datetime.today().day).zfill(2)
                          + "09"  # to receive notifications at 9a.m.
                          )
            with open(counts_dir + chat_id + db_file, 'a') as db:
                db.write("0\n0\n")  # at least 2 entries needed
            logger.info("New group added to the database: " + chat_id)

        # text and caption are mutually exclusive so at least one is None
        text = update.message.text
        caption = update.message.caption
        if text is not None:
            asd_increment = text.lower().count("asd")
        elif caption is not None:
            asd_increment = caption.lower().count("asd")
        else:
            asd_increment = 0

        if 0 < asd_increment < 10:
            try:
                asd_count, date, week_start = get_current_count_content(chat_id)
                logger.info(str(asd_count) + date)
                with open(counts_dir + chat_id + cnt_file, 'w') as f:
                    asd_count += asd_increment
                    f.write(str(asd_count)
                            + " "
                            + date)
                logger.info("asd counter increased to " + str(asd_count))

            except Exception as e:
                bot.send_message(chat_id=castes_chat_id, text="asd_counter_bot si è sminchiato perché:\n" + str(e))
                logger.error(e, file=stderr)


def notify(bot):
    """
    this function is called at the launch of the script in the main function as a separate process
    this function is NOT to be called by a Message or Command Handler
    we use time.sleep() with the number of seconds until the day after the date found in current_count.txt
    at the same hour, until it's Monday
    then notify group with a random phrase based on asd increase or decrease
    """
    while True:
        try:
            # first, sleep until 5am
            time_to_sleep = calculate_time_to_sleep(hour=5, minute=0)
            sleep(time_to_sleep)

            # then, sleep until desired hour - this should compute the correct hour
            # even for the days when the hour changes
            with open(group_db, 'r') as g_db:
                # every chat_id has the same start date in this simplified version
                first_chat_id = g_db.readlines()[0].split("\n")[0]
                *_, start = get_current_count_content(first_chat_id)

            time_to_sleep = calculate_time_to_sleep(hour=start.hour, minute=0)
            logger.info(str(time_to_sleep) + " daily")
            sleep(time_to_sleep)

            weekday = datetime.today().strftime("%A")
            if weekday != "Monday":
                logger.info("Skipping notification on " + weekday)
                continue

            # this is because the message is set to be weekly
            td = timedelta(days=7)
            with open(group_db, 'r') as g_db:
                for chat_id in g_db.readlines():
                    chat_id = chat_id.split("\n")[0]  # ignore \n at end of line
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

                    stats = "\n\nQuesta settimana abbiamo totalizzato " + str(past_period_asd_count) + " asd"
                    diff = str(abs(past_period_asd_count - _period_before_that_asd_count))
                    if past_period_asd_count == _period_before_that_asd_count:
                        reply = random.choice(equals)
                        end = ", proprio come la scorsa settimana!"
                    elif past_period_asd_count > _period_before_that_asd_count:
                        reply = random.choice(ismore)
                        end = ", ossia " + str(diff) + " asd in più rispetto alla scorsa settimana!"
                    else:  # past_week_asd_count < _week_before_that_asd_count:
                        reply = random.choice(isless)
                        end = ", ossia " + str(diff) + " asd in meno rispetto alla scorsa settimana. D'oh!"
                    bot.send_message(chat_id=chat_id, text=reply + stats + end)
                    history_graph(bot, None, chat_id)

        except Exception as e:
            bot.send_message(chat_id=castes_chat_id, text="asd_counter_bot si è sminchiato perché:\n" + str(e))
            logger.info(e, file=stderr)


def why(bot, update):
    """Explain what asd means for our society and our future"""
    bot.send_message(chat_id=update.message.chat_id,
                     text='Why not? Asd\n'
                          '<a href="https://nonciclopedia.org/wiki/Asd">Assorbi il sapere ITALIANO</a>\n'
                          '<a href="https://www.urbandictionary.com/define.php?term=asd">Risucchia la knowledge MMERRICANA</a>\n'
                          '<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ">Spiegazione ultramegadettagliata the best</a>\n',
                     parse_mode="HTML",
                     disable_web_page_preview=True)


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
    dp.add_handler(CommandHandler("record", print_record))
    dp.add_handler(CommandHandler("average", print_average))
    dp.add_handler(CommandHandler("total", print_total))
    dp.add_handler(CommandHandler("graph", history_graph))
    dp.add_handler(CommandHandler("why", why))
    dp.add_handler(CommandHandler("help", help))
    # for every message
    dp.add_handler(MessageHandler((Filters.text | Filters.photo | Filters.video | Filters.document) & Filters.group,
                                  asd_counter))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    updater_process = Process(target=updater.idle)
    notify_process = Process(target=notify, args=(bot.Bot(token),))  # comma needed to make tuple

    updater_process.start()
    notify_process.start()
    updater_process.join()
    notify_process.join()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.


if __name__ == '__main__':
    main()
