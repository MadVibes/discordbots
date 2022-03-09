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


db_schema = {
  "bets": []
}

#data = Database(logger, config['DATA_STORE'], db_schema)

class Bot:
  def __init__(self, logger: Logger, config, bank, client: discord.Client):
      self.logger = logger
      self.config = config
      self.client = client
      self.bank = bank
      self.guild_id = 0
    
  async def bet(self, ctx, args):
    args = ' '.join(args)
    if not len(args):
      await ctx.send("poo brain")
      
    elif args[0] == "create":
      args.pop(0)
      for word in args:
        if word.isdigit():
          pos = args.index(word)
          wager = int(word)
          args.pop(pos)
          
      user_balance = self.bank.getBalance(ctx.author.id)
      # insufficient balance
      if int(wager) >= user_balance:
          await ctx.reply(f'Insufficient balance, current balance is {user_balance} VBC')
          return
      try:
          self.bank.spendCurrency(ctx.author.id, wager)
          await make_bet(ctx, args, wager)
          
      except Exception as e:
          self.logger.warn('Failed to execute bet:')
          self.logger.warn(str(e))


async def make_bet(ctx, args, wager):
  data1 = data.read()
  print(data1)

'''
  balance = 0
  for user in data['users']:
      if user['user_id'] == user_id:
          user['balance'] += amount
          balance = user['balance']
  self.data.write(data)
  return balance



# FIGURE THIS OUT LATER
def user_id_exists(self, user_id: int):
      """Does user name exist"""
      data = self.data.read()
      for user in data['users']:
          if user['user_id'] == user_id:
              return True
      return False'''