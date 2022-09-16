"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from datetime import datetime

from telegram import __version__ as TG_VER
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from hidden import get_token
from utils import checkLevelUp, checkLevelDown, getExpForLvlUp, checkTime, getRandomMsg, getTimeDifference, saveCheckTime, makeRoll, addExp, getLastCheck, getLevel, getDungeonUserInfo, scaleRoll


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def stepIntoDungeon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main functionality function. Represents a user trying 
    to step into the dungeon.
    
    If it passed enough of time since last attempt, go into the 
    dungeon, make a roll to get/lose exp, add rolled amount of exp
    to the database, and send a message of it to the user.
    
    If not enough time passed the user sends a message with 
    the time left to wait until next attempt.
    """
    # 1. Get the user's last check time from the database
    # if there is no user there -- add them
    # 2. Check the time for a roll and make a roll 
    # if enough time passed
    # 3. If there was a roll -- save new exp and level 
    # if there was enough exp to level up

    # Get user's id
    user = update.effective_user
    user_id = user['id']
    user_fname = user['first_name']

    # Check current exp and last check time
    last_check = getLastCheck(user_id) # In ISO format

    msg = f'{user_fname} | '
    # Check if it's been enough time since last check
    time_check = checkTime(last_check)
    if time_check != None:

        # Save new check time
        saveCheckTime(user_id, time_check)

        # Roll for some exp and scale it according to user's lvl
        roll = makeRoll()
        roll = scaleRoll(user_id, roll)
        if roll > 0:
            table_bool = True
        else:
            table_bool = False
        
        # Get a random message depending on the win or lose
        msg += f'{getRandomMsg(table_bool)} |'
        
        if table_bool:
            msg += f' Experience Gained: {roll} 💎'
        elif roll == 0:
            msg += f' No Experience Gained 😔'
        else:
            msg += f' Experience Lost: {roll} 😔'
    
        # Add rolled amount to the current exp amount in the db
        if roll != 0:
            addExp(user_id, roll)

            # Send a message if there was a level up
            if checkLevelUp(user_id):
                level = getLevel(user_id)
                await update.message.reply_text(f'{user_fname} | You gained enough exp to level up! Your Level now is {level} 💎')

            # Send a message if there was a level down
            if checkLevelDown(user_id):
                level = getLevel(user_id)
                await update.message.reply_text(f'{user_fname} | You lost too much exp and leveled down. Your Level now is {level} 😔')
    else:
        # Return how much time left until the next entering
        next_check = getTimeDifference(last_check)
        msg += f'You have already entered the dungeon recently, {next_check} left until you can enter again! ⌛'

    await update.message.reply_text(msg)


async def sendDungeonInfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with current total exp and level of the user."""

    # Get user's id
    user = update.effective_user
    user_id = user['id']
    user_fname = user['first_name']

    current_exp, current_level = getDungeonUserInfo(user_id)
    exp_to_lvl = getExpForLvlUp(user_id)
    msg = f'{user_fname} | You are currently Level {current_level}. Total Exp: {current_exp} EXP ⚔️\n'
    msg+= f'To achieve Level {current_level + 1} you need: {exp_to_lvl}.'

    await update.message.reply_text(msg)



def main() -> None:
    """Start the bot."""
    token = get_token()
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # On different commands - answer in Telegram
    application.add_handler(CommandHandler("ed", stepIntoDungeon))
    application.add_handler(CommandHandler("exp", sendDungeonInfo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()