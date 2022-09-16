# All helper functions for a bot's functionality

import sqlite3, timedelta, random
from datetime import datetime
from datetime import timedelta as classic_td
from hidden import get_db_name

# Get db's file name from the hidden file
DB_NAME = get_db_name()

def getExp(user_id):
    '''
    Return current amount of exp for the passed user.

    If there is no user in the db, add them there.
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute('SELECT total_exp FROM dungeon_users WHERE user_id=?', (user_id,))
    row = cur.fetchall()
    
    # Add user to the database if unable 
    # to get any data from it
    if len(row) == 0:
        addUser(user_id, 'dungeon_users')
        return None

    cur.close()
    conn.close()

    return row[0][0]


def getLastCheck(user_id, table_name):
    '''
    Return last check time for the passed user in the given table.

    Passed arguments: user_id, table_name in the db.
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(f'SELECT last_check FROM {table_name} WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    last_check = row[0]

    cur.close()
    conn.close()

    return last_check
    

def addExp(user_id, points, table_name, column_name):
    '''
    Adds a given amount of exp/points to the given user in the 
    database, table's name, and name of the column which stores 
    exp/points.

    Needed arguments: user's id in the db, amount 
    of added points
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    total_exp = getExp(user_id)
    total_exp_upd = total_exp + points 

    cur.execute(f'UPDATE {table_name} SET {column_name} = ? WHERE user_id = ?', 
                (total_exp_upd, user_id,))
    conn.commit()

    cur.close()
    conn.close()


def addUser(user_id, table_name):
    '''
    Create an instance in the given table in the database 
    for a given user.
    
    Passed arguments: user_id, table_name.
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(f'INSERT OR IGNORE INTO {table_name} (user_id) VALUES (?)', (user_id,))
    conn.commit()

    cur.close()
    conn.close()


def checkTime(last_check, time_in_sec):
    '''
    Check if it's been more than 1 hour since last check. 
    Takes last check in ISO format, time to compare with 
    in seconds.
    
    Returns current datetime object or None.
    '''

    # Create instance from the given time and today's time
    last = datetime.fromisoformat(last_check)
    today = datetime.today()

    # Convert to timedelta instance
    td = timedelta.Timedelta(today - last)

    # Check in order to avoid the bug when it doesn't know 
    # that it's negative time
    diff = getTimeDifference(last_check) 
    if '-' in diff:
        return today

    # Do the actual check
    if td.total.total_seconds <= time_in_sec:
        datetime.fromisoformat(last_check)
        return None

    return today


def saveCheckTime(user_id, today, table_name):
    '''
    Save current check time to the database.
    
    Takes user's id in the database, the current datetime object, 
    and table's name as arguments.
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    today_iso = today.isoformat()

    cur.execute(
                f'UPDATE {table_name} SET last_check = ? WHERE user_id = ?', 
                (today_iso, user_id))
    conn.commit()

    cur.close()
    conn.close()


def getTimeDifference(last_check):
    '''
    Return a string of how much time is left before 
    user can do a next roll.

    Returns str in format HH:MM:SS.
    '''
    # Create instance from the given time and today's time
    last = datetime.fromisoformat(last_check)
    one_min = classic_td(hours=1)
    today = datetime.now()

    next_check = last + one_min
    next_check = next_check - today
    # Prepare a string with left time in format HH:MM:SS
    # by convert it to str and removing miliseconds
    next_check_str = str(next_check)[:-7]

    return next_check_str


def makeRoll():
    '''Return a generated roll.'''
    
    # Roll a random number from 0 to 99
    roll = random.random() * 10e15
    roll = int(roll % 100)

    if roll < 25:
        # Roll how many to lose and return it
        return rollHowMany() * -1
    elif roll >= 95:
        # Neither get nor lose
        return 0
    else:
        # Roll how many to get and return it
        return rollHowMany()


def rollHowMany():
    '''Roll how many exp to get or lose.'''

    roll = random.random() * 10e15
    roll = int(roll % 70)

    # If it's too small, make roll a minimum amount
    if roll < 20:
        roll = 20
    
    return roll


def getRandomMsg(checkBool):
    '''
    Return a random message in string format from the database.
    
    Takes a boolean argument. If True -- returns a positive outcome, 
    if False -- a negative one.
    '''
    # Decide which table to choose based on passed bool value
    if checkBool:
        db_pos_or_neg = 'dungeon_encounters_pos'
    else:
        db_pos_or_neg = 'dungeon_encounters_neg'

    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Get total amount of rows
    cur.execute(f'SELECT COUNT(id) from {db_pos_or_neg}')
    row = cur.fetchone()
    total_encs = row[0]

    # Roll a random number in this range
    roll = random.random() * 10e15
    roll = int(roll % total_encs)

    # Take a message at this number
    cur.execute(f'SELECT message FROM {db_pos_or_neg} WHERE id=?', (roll + 1,))
    row = cur.fetchone()
    result_enc = row[0]

    cur.close()
    conn.close()

    return result_enc


def addRow(value, column_name, table_name):
    '''
    Adds a new value into the database in the row 
    with only 1 column.
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(f'INSERT OR IGNORE INTO {table_name} ({column_name}) VALUES (?)', (value, ))
    conn.commit()

    cur.close()
    conn.close()


def getLevel(user_id):
    '''Return a current level of the passed user.'''
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute('SELECT current_level FROM dungeon_users WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    current_lvl = row[0]

    cur.close()
    conn.close()

    return current_lvl


def scaleRoll(user_id, roll):
    '''Scale a rolled amount of exp according to a user's level.'''
    current_lvl = getLevel(user_id)

    for i in range(current_lvl):
        roll *= 1.05
    
    return int(roll)


def checkLevelUp(user_id):
    '''
    Level up if there is enough exp.

    Return True if there was a level up and False if not.
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Get current level
    cur.execute('SELECT current_level FROM dungeon_users WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    current_level = row[0]

    # Get amount of exp for the next level up
    cur.execute('SELECT total_exp FROM dungeon_levels WHERE level=?', (current_level + 1,))
    row = cur.fetchone()
    exp_to_lvl_up = row[0]

    current_exp = getExp(user_id)

    # Check if there's enough exp to level up
    # if yes save new value in the db
    if current_exp >= exp_to_lvl_up:
        cur.execute('UPDATE dungeon_users SET current_level = ? WHERE user_id = ?', (current_level + 1, user_id))
        conn.commit()
        result = True
    else:
        result = False

    cur.close()
    conn.close()

    return result


def checkLevelDown(user_id):
    '''
    Lose level if user lost enough exp.

    Return True if there was a level up and False if not.
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Get current level
    cur.execute('SELECT current_level FROM dungeon_users WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    current_level = row[0]

    # Finish the check preemptively if the level is 1 -- the minimum level to have
    if current_level == 1:
        cur.close()
        conn.close()
        return False

    # Get amount of exp for the current level
    cur.execute('SELECT total_exp FROM dungeon_levels WHERE level=?', (current_level,))
    row = cur.fetchone()
    exp_to_lvl_up = row[0]

    current_exp = getExp(user_id)
    # Check if there's not enough exp for the current level
    # if yes save new value in the db
    if current_exp < exp_to_lvl_up:
        cur.execute('UPDATE dungeon_users SET current_level = ? WHERE user_id = ?', (current_level - 1, user_id))
        conn.commit()
        result = True
    else:
        result = False

    cur.close()
    conn.close()

    return result


def getDungeonUserInfo(user_id):
    '''Return a tuple of user's total experience and level.'''
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute('SELECT total_exp, current_level FROM dungeon_users WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    current_exp = row[0]
    current_level = row[1]

    cur.close()
    conn.close()

    return current_exp, current_level


def getExpForLvlUp(user_id):
    '''
    Return a integer value of exp amount needed for the next 
    level up.
    '''
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Get a current level of the passed user
    cur.execute('SELECT current_level FROM dungeon_users WHERE user_id=?', (user_id,))
    row = cur.fetchone()
    current_level = row[0]

    # Get a needed amount exp to level up
    cur.execute('SELECT total_exp FROM dungeon_levels WHERE level=?', (current_level + 1,))
    row = cur.fetchone()
    exp = row[0]

    cur.close()
    conn.close()

    return exp
