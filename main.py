from datetime import date, datetime, timedelta
import logging
import os
import re

from dotenv import load_dotenv
from telegram import Update, error
from telegram.ext import \
    ApplicationBuilder, \
    CallbackContext, \
    CommandHandler, \
    ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    remove_job_if_exists(str(update.effective_chat.id), context)

    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    tomorrow = today + timedelta(days=1, seconds=5)

    context.job_queue.run_repeating(
        happy_birthday,
        24 * 60 * 60,
        first=tomorrow,
        chat_id=update.effective_chat.id,
        name=str(update.effective_chat.id)
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Bot started'
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    job_removed = remove_job_if_exists(str(update.effective_chat.id), context)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Bot stopped'
    )


async def happy_birthday(context: CallbackContext) -> None:
    '''Say happy birthday, if necessary'''
    with open('birthdays.csv') as f:
        lines = f.readlines()

    now = datetime.now()
    for line in lines:
        uid, name, birthday = line.split(',')
        uid = int(uid)

        month, day, year = birthday.split('/')
        month, day, year = int(month), int(day), int (year)
        birthday = date(year, month, day)

        if now.month == birthday.month and now.day == birthday.day:
            try:
                name = (await context.bot.get_chat_member(
                    chat_id=context.job.chat_id,
                    user_id=uid
                )).user.mention_html()
            except error.BadRequest:
                pass
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f'Happy Birthday {name}!',
                parse_mode='HTML'
            )


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    '''Remove job with given name. Returns whether job was removed.'''
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def main() -> None:
    '''Start the bot.'''
    load_dotenv()
    TOKEN = os.getenv('TOKEN')

    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stop', stop))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == '__main__':
    main()
