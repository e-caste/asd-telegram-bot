"""
"asd"
    - cit. Anonimo il 6/9/69 d.C. alle 4.20pm
"""

# TODO: implement command handler for /record - number has to be saved to a separate file

import logging
from telegram import bot, chat
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from robbamia import *
from datetime import datetime, timedelta
import time
import threading
from motivational_replies import *
import random

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

"""START TEST"""
# test = "asd ciao come va ASD testaSd"
# print(test.lower().count("asd"))
# exit(33)

# test_date = datetime(year=2019, month=4, day=29, hour=9)
# print(test_date + timedelta(days=7))
# exit(33)

# db = open("past_asd.txt", 'r')
# print(db.readlines()[-2].split("\t")[0])
# db.close()
# exit(33)

# with open("current_count.txt", 'r') as f:  # 'rw' is forbidden
#     # 0 2019040809
#     content = f.read().split(" ")
# print(content)
# exit(33)
"""END TEST"""

def get_current_count_content():
    with open("current_count.txt", 'r') as f:  # 'rw' is forbidden
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

def asd_counter(bot, update):
    """
    this function increases the asd_count and writes it to disk
    when a new message on the filtered group contains at least 1 "asd"
    """
    if update.message.chat.type == chat.Chat.SUPERGROUP and \
            update.message.chat.title == "WEEE Chat":
        print(update.message.chat.title + " " + str(update.message.chat_id))
        asd_increment = update.message.text.lower().count("asd")
        if asd_increment > 0:
            try:
                asd_count, date, week_start = get_current_count_content()
                print(asd_count, date)
                with open("current_count.txt", 'w') as f:
                    asd_count += asd_increment
                    f.write(str(asd_count)
                            + " "
                            + date)
                print("asd counter increased to " + str(asd_count))

            except Exception as e:
                bot.send_message(chat_id=castes_chat_id, text="asd_counter_bot si è sminchiato perché:\n" + str(e))
                print(e)

def notify_weekly(bot):
    """
    this function is called at the launch of the script in the main function as a separate thread
    this function is NOT to be called by a Message or Command Handler
    we use time.sleep() with the number of seconds until the date found in current_count.txt
    + timedelta(days=7) - datetime.now()
    then notify group with a random phrase based on asd increase or decrease
    """
    while True:
        try:
            *_, week_start = get_current_count_content()
            time_to_sleep = int((week_start + timedelta(days=7) - datetime.now()).total_seconds())
            print(time_to_sleep)
            time.sleep(time_to_sleep)
            # time.sleep(5)
            # UPDATE asd_count VARIABLE AFTER SLEEPING
            asd_count, *_ = get_current_count_content()
            # UPDATE DATABASE - append weekly result
            with open("past_asd.txt", 'a') as db:
                db.write("\n" + str(asd_count)
                         + "\t"
                         + str(week_start)
                         + " - "
                         + str(week_start + timedelta(days=7)))
            week_start += timedelta(days=7)
            # UPDATE CURRENT COUNTER - overwrite and reset to 0
            with open("current_count.txt", 'w') as f:
                f.write(str(0)
                        + " "
                        + str(week_start.year).zfill(4)
                        + str(week_start.month).zfill(2)
                        + str(week_start.day).zfill(2)
                        + str(week_start.hour).zfill(2))
            # READ 2 LATEST RESULTS FROM DATABASE
            with open("past_asd.txt", 'r') as db:
                past_week_asd_count = asd_count
                _week_before_that_asd_count = int(db.readlines()[-2].split("\t")[0])

            stats = "\n\nQuesta settimana abbiamo totalizzato " + str(past_week_asd_count) + " asd"
            diff = str(abs(past_week_asd_count - _week_before_that_asd_count))
            if past_week_asd_count == _week_before_that_asd_count:
                reply = random.choice(equals)
                end = ", proprio come la scorsa settimana!"
            elif past_week_asd_count > _week_before_that_asd_count:
                reply = random.choice(ismore)
                end = ", ossia " + str(diff) + " asd in più rispetto alla scorsa settimana!"
            else: # past_week_asd_count < _week_before_that_asd_count:
                reply = random.choice(isless)
                end = ", ossia " + str(diff) + " asd in meno rispetto alla scorsa settimana. D'oh!"
            bot.send_message(chat_id=weee_chat_chat_id, text=reply+stats+end)

        except Exception as e:
            bot.send_message(chat_id=castes_chat_id, text="asd_counter_bot si è sminchiato perché:\n" + str(e))
            print(e)

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
    dp.add_handler(CommandHandler("help", help))
    # for every message
    dp.add_handler(MessageHandler(Filters.text & Filters.group, asd_counter))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    t1 = threading.Thread(target=updater.idle)
    t2 = threading.Thread(target=notify_weekly(bot.Bot(token)))

    t1.start()
    t2.start()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()


if __name__ == '__main__':
    main()