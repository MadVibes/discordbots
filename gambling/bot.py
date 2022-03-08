# This handles the actual bot logic
####################################################################################################
from datetime import datetime
import configparser
import sys
import discord


sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger
from lib.data import Database
from lib.bank_interface import Bank

# CONFIGS/LIBS
########################################################################################################
bot_type = 'croupier'
config = configparser.ConfigParser()
config.read('./config.ini') # CHANGE ME
config = config[bot_type]

VERSION = 'v1.0'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

logger = Logger(int(config['LOGGING_LEVEL']), bool(config['WRITE_TO_LOG_FILE']), config['LOG_FILE_DIR'])
if ('LOGGING_PREFIX' in config and 'LOGGING_PREFIX_SIZE' in config):
    logger.custom_prefix = config['LOGGING_PREFIX']
    logger.custom_prefix_size = int(config['LOGGING_PREFIX_SIZE'])
logger.log(f'Starting {bot_type} - ' + VERSION)
bank = Bank(logger, config)

db_schema = {
  "bets": []
}

data = Database(logger, config['DATA_STORE'], db_schema)

async def bet(ctx, *, args=None):
  if args == None:
    pass
    
  elif args[0] == "create":
    args.pop(0)
    for word in args:
      if word.isdigit():
        pos = args.index(word)
        wager = int(word)
        args.pop(pos)
        
    user_balance = bank.getBalance(ctx.author.id)
    # insufficient balance
    if int(wager) >= user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} VBC')
        return
    try:
        bank.spendCurrency(ctx.author.id, wager)
        await make_bet(ctx, args, wager)
        
    except Exception as e:
        logger.warn('Failed to execute bet:')
        logger.warn(str(e))


async def make_bet(ctx, args, wager):
  
# FIGURE THIS OUT LATER
  def user_id_exists(self, user_id: int):
        """Does user name exist"""
        data = self.data.read()
        for user in data['users']:
            if user['user_id'] == user_id:
                return True
        return False

  def alter_balance(self, amount: int, user_id: int):
        """Alter balance by amount"""
        data = self.data.read()
        balance = 0
        for user in data['users']:
            if user['user_id'] == user_id:
                user['balance'] += amount
                balance = user['balance']
        self.data.write(data)
        return balance