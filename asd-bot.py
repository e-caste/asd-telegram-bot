"""
"asd"
    - cit. Anonimo il 6/9/69 d.C. alle 4.20pm
"""

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler
from robbamia import token, castes_chat_id
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    bot.send_message(chat_id=update.message.chat_id, text='Hi ' + update.message.from_user.first_name +
                                                          ', welcome to asd bot!')

def asd_counter(bot, update):
    """
    if date of first msg has timedelta > 24h with respect to datetime.now() send data to past_asd.txt
    else increase count
    """
    if "asd" in update.message.text.lower():
        try:
            f = open("count.txt", 'rw')
            asd_count = int(f.read().split(" ")[0])
            # 0 2019040809
            date = f.read().split(" ")[1]
            week_start = datetime(year=int(date[0:3]),
                                  month=int(date[4:5]),
                                  day=int(date[6:7]),
                                  hour=int(date[8:9]))
            if (week_start - datetime.now()).seconds > 604800: # seconds in 1 week
                db = open("past_asd.txt", 'w')
                db.write(str(asd_count)
                         + str(week_start)
                         + " - "
                         + str(week_start + timedelta(days=7))) # TODO: append
                db.close()
                asd_count = 1
                week_start += timedelta(days=7)
                f.write(str(asd_count) + " "    # TODO: overwrite
                        + str(week_start.year)
                        + str(week_start.month)
                        + str(week_start.day)
                        + str(week_start.hour))
            else:
                asd_count += 1
                f.write(str(asd_count)
                        + " "
                        + date) # TODO: overwrite

            f.close()

        except Exception as e:
            bot.send_message(chat_id=castes_chat_id, text="asd_count_bot si è sminchiato\n" + str(e))

def notify_weekly(bot):
    pass
    # TODO: add text to WEEE Chat

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
    dp.add_handler(MessageHandler(asd_counter))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()