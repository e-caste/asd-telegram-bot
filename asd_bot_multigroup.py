"""
"asd"
    - cit. Anonimo il 6/9/69 d.C. alle 4.20pm
"""

import logging
from datetime import datetime, timedelta
import calendar
from dateutil import tz
import random
import os
from subprocess import Popen
from typing import Union

from telegram import bot, chat, Update, TelegramError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, JobQueue
from telegram.error import BadRequest
import matplotlib.pyplot as plt

from motivational_replies import *

# import Docker environment variables
token = os.environ["TOKEN"]
castes_chat_id = os.environ["CST_CID"]
counts_dir = os.environ["COUNTS_DIR"]
group_db = os.environ["GROUP_DB"]
db_file = os.environ["DB_FILE"]
cnt_file = os.environ["CNT_FILE"]
graph_file = os.environ["GRAPH_FILE"]
DEBUG = os.environ.get("DEBUG")

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
    try:
        lol_count = int(content[2])
    except IndexError:
        lol_count = 0
    return asd_count, date, week_start, lol_count


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    context.bot.send_message(chat_id=update.message.chat_id, text='Ciao ' + update.message.from_user.first_name +
                                                          ', benvenuto su asd bot! Conto solo gli asd dei gruppi'
                                                          ' dove sono presente, quindi a te ora non servo a nulla asd')


def print_record(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    record = -1
    with open(counts_dir + chat_id + db_file, 'r') as db:
        for line in db.readlines():
            record = max(record, int(line.split("\t")[0]))
    context.bot.send_message(chat_id=chat_id, text="Il nostro record attuale di asd settimanali è di "
                                           + str(record) + " asd. Asdate di più per batterlo!")


def print_average(update: Update, context: CallbackContext) -> None:
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
    context.bot.send_message(chat_id=chat_id, text="La nostra media attuale di asd settimanali è di "
                                           + str(avg) + " asd. Asdate di più per alzarla!")


def print_total(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    sum = 0
    with open(counts_dir + chat_id + db_file, 'r') as db:
        for line in db.readlines():
            sum += int(line.split("\t")[0])
    current_count, *_ = get_current_count_content(chat_id)
    sum += current_count
    context.bot.send_message(chat_id=chat_id, text="Il nostro totale attuale di asd è di "
                                                   + str(sum) + " asd.")


def history_graph(update: Union[Update, None], context: CallbackContext, chat_id: str = "") -> None:
    # the function has been invoked by a user, otherwise it has been invoked by notify()
    show_from_beginning = chat_id == ""
    if show_from_beginning:
        chat_id = str(update.message.chat_id)

    db_path = os.path.join(counts_dir, chat_id + db_file)
    if not os.path.exists(db_path):
        context.bot.send_message(chat_id=chat_id, text="Non ci sono statistiche salvate per questa chat. "
                                                       "Prova in un gruppo dove sono presente! Asd")
    x, y_asd, y_lol = [], [], []
    with open(db_path, 'r') as db:
        for line in db.readlines()[2:]:  # skips first 2 lines which only contain a 0
            try:
                # starting date
                x.append(str(line.split("- ")[1].split(" ")[0]))
                # number of asds and lols
                y_asd.append(int(line.split("\t")[0]))
                try:
                    y_lol.append(int(line.split("\t")[2]))
                except (IndexError, ValueError):
                    y_lol.append(0)
            # skip groups that have wrongly formatted or no data
            except IndexError as ie:
                logger.warning(f"IndexError while reading {db_path} to make a graph", exc_info=True)
                return

    if not show_from_beginning:
        # only show the last half year progress when sending notification
        x = x[-26:]
        y_asd = y_asd[-26:]
        y_lol = y_lol[-26:]
        step = 1
    else:
        # only show 1 in step labels for readability
        step = (len(x) // 50) + 1
    
    with plt.xkcd():
        plt.plot(x, y_asd, label="ASDs", linestyle="-")
        plt.plot(x, y_lol, label="LOLs", linestyle="--")
        plt.legend()
        plt.xticks(range(0, len(x), step), rotation=90)
        plt.tick_params(axis='x', which='major', labelsize=8)
        plt.tight_layout()
        path_to_graph = os.path.join(counts_dir, chat_id + graph_file)
        if os.path.exists(path_to_graph):
            Popen(["rm", path_to_graph])
        plt.savefig(path_to_graph, dpi=300, bbox_inches='tight')
        # close figure
        plt.close()

    context.bot.send_photo(chat_id=chat_id, photo=open(path_to_graph, 'rb'))


def asd_counter(update: Update, context: CallbackContext) -> None:
    """
    this function increases the asd_count and writes it to disk
    when a new message on the filtered group contains at least 1 "asd"
    """
    if update.message.chat.type == chat.Chat.SUPERGROUP or \
            update.message.chat.type == chat.Chat.GROUP:
        logger.info(update.message.chat.title + " " + str(update.message.chat_id))

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
            logger.info(f"New group added to the database: {chat_id}")

        if update.message.sticker:
            asd_increment, lol_increment = 0, 0
            if update.message.sticker.set_name == "weeeopen" \
                    and update.message.sticker.emoji in (
                    "🤣",  # catalizzatore
                    "📬",  # mail
            ):
                lol_increment = 1
        else:
            # text and caption are mutually exclusive so at least one is None
            text = update.message.text
            caption = update.message.caption
            source = text or caption or ""

            asd_increment = sum([source.lower().count(s) for s in ("asd", "æsd", "a.s.d", "a s d")])
            lol_increment = sum([source.lower().count(s) for s in ("lol", "lil", "lel", "læl", "lael")])

        if 0 < (asd_increment + lol_increment) <= 20:
            try:
                asd_count, date, week_start, lol_count = get_current_count_content(chat_id)
                with open(counts_dir + chat_id + cnt_file, 'w') as f:
                    asd_count += asd_increment
                    lol_count += lol_increment
                    f.write(f"{asd_count} {date} {lol_count}")
                logger.info(" & ".join(filter(None, [f"asd counter increased to {asd_count}" if asd_increment else "",
                                                     f"lol counter increased to {lol_count}" if lol_increment else ""])))

            except Exception as e:
                context.bot.send_message(chat_id=castes_chat_id, text=f"asd_counter_bot si è sminchiato perché:\n{e}")
                logger.error(e, exc_info=True)


def notify(context: CallbackContext) -> None:
    try:
        with open(group_db, 'r') as g_db:
            # every chat_id has the same start date in this simplified version
            first_chat_id = g_db.readlines()[0].split("\n")[0]
            *_, start, _ = get_current_count_content(first_chat_id)

        # this is because the message is set to be weekly
        td = timedelta(days=7)
        with open(group_db, 'r') as g_db:
            try:
                for chat_id in g_db.readlines():
                    chat_id = chat_id.split("\n")[0]  # ignore \n at end of line
                    # UPDATE asd_count VARIABLE AFTER SLEEPING
                    asd_count, *_, lol_count = get_current_count_content(chat_id)
                    # UPDATE DATABASE - append weekly result
                    with open(counts_dir + chat_id + db_file, 'a') as db:
                        db.write(f"\n{asd_count}\t{start} - {start + td}\t{lol_count}")
                    start += td
                    # UPDATE CURRENT COUNTER - overwrite and reset to 0
                    with open(counts_dir + chat_id + cnt_file, 'w') as f:
                        f.write(f"0 {str(start.year).zfill(4)}{str(start.month).zfill(2)}"
                                f"{str(start.day).zfill(2)}{str(start.hour).zfill(2)} 0")
                    # READ 2 LATEST RESULTS FROM DATABASE
                    with open(counts_dir + chat_id + db_file, 'r') as db:
                        past_period_asd_count = asd_count
                        past_period_lol_count = lol_count
                        try:
                            _period_before_that_asd_count = int(db.readlines()[-2].split("\t")[0])
                        except ValueError:
                            continue

                    stats = f"Questa settimana abbiamo totalizzato {past_period_asd_count} asd"
                    diff = abs(past_period_asd_count - _period_before_that_asd_count)
                    if past_period_asd_count == _period_before_that_asd_count:
                        reply = random.choice(equals)
                        end = ", proprio come la scorsa settimana!"
                    elif past_period_asd_count > _period_before_that_asd_count:
                        reply = random.choice(ismore)
                        end = f", ossia {diff} asd in più rispetto alla scorsa settimana!"
                    else:  # past_week_asd_count < _week_before_that_asd_count:
                        reply = random.choice(isless)
                        end = f", ossia {diff} asd in meno rispetto alla scorsa settimana. D'oh!"

                    if asd_count > lol_count:
                        asd_vs_lol_msg = f"L'asd faction ha sconfitto il malvagio lollone di ben " \
                                         f"{asd_count - lol_count} unità! Gioite popolol... Whoops, intendevo " \
                                         f"famigliasd"
                    elif asd_count < lol_count:
                        asd_vs_lol_msg = f"La lollone faction ha trionfato sulla fazione dell'asd di appena " \
                                         f"{lol_count - asd_count} lols. Tornerà forse l'asd in vetta la prossima " \
                                         f"settimana? Only grr reactions per la famigliasd per ora... 😡😡😡"
                    else:
                        asd_vs_lol_msg = f"Questa settimana gli asd e i lol sono stati \"perfectly balanced, as all " \
                                         f"memes should be...\" Per l'esattezza, ci sono stati {asd_count} asd/lol, " \
                                         f"tra cui probabilmente degli æsd e dei lolloni colossali!"

                    try:
                        context.bot.send_message(chat_id=chat_id, text="\n\n".join([reply, stats + end, asd_vs_lol_msg]))
                        history_graph(None, context, chat_id)
                    except BadRequest as br:
                        logger.warning(f"Skipping {chat_id} because:\n{br}", exc_info=True)

                if DEBUG:
                    exit()

            except TelegramError as te:
                logger.warning(f"Skipping {chat_id} because:\n{te}", exc_info=True)

    except Exception as e:
        context.bot.send_message(chat_id=castes_chat_id, text=f"asd_counter_bot si è sminchiato perché:\n{e}")
        logger.error(e, exc_info=True)


def why(update: Update, context: CallbackContext) -> None:
    """Explain what asd means for our society and our future"""
    context.bot.send_message(chat_id=update.message.chat_id,
                     text='Why not? Asd\n'
                          '<a href="https://nonciclopedia.org/wiki/Asd">Assorbi il sapere ITALIANO</a>\n'
                          '<a href="https://www.urbandictionary.com/define.php?term=asd">Risucchia la knowledge MMERRICANA</a>\n'
                          '<a href="https://weee.link/asd">Spiegazione ultramegadettagliata the best</a>\n',
                     parse_mode="HTML",
                     disable_web_page_preview=True)


def help(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    context.bot.send_message(chat_id=update.message.chat_id, text='https://youtu.be/cueulBxn1Fw')


def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token)
    job_queue: JobQueue = updater.job_queue

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
    dp.add_handler(MessageHandler(
        (Filters.text | Filters.photo | Filters.video | Filters.document | Filters.sticker) & Filters.group,
        asd_counter
    ))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # run weekly group notification job
    next_monday = datetime.today() + timedelta((calendar.MONDAY - datetime.today().weekday()) % 7)
    run_first_datetime = datetime(year=next_monday.year,
                                  month=next_monday.month,
                                  day=next_monday.day,
                                  hour=9,
                                  tzinfo=tz.gettz("Europe/Rome"))
    job_queue.run_repeating(notify,
                            interval=timedelta(weeks=1),
                            first=run_first_datetime)
    # print(job_queue.get_jobs_by_name("notify")[0].next_t.astimezone(tz.gettz("Europe/Rome")))

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
