# This handles the actual bot logic
####################################################################################################
from datetime import datetime
import configparser
import sys
import discord
import re


sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger
from lib.data import Database
from lib.bank_interface import Bank


db_schema = {
  "bets": []
}


class Bot:
  def __init__(self, logger: Logger, config, bank, client: discord.Client):
    self.logger = logger
    self.config = config
    self.client = client
    self.bank = bank
    self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)

  # Embed for bets
  async def bet_embed(self, ctx, data):
    embed = discord.Embed(
      title='All Bets',
      description='-------',
      colour=discord.Colour.green()
    )

    for i in data["bets"]:
      id = i['ID']
      title = str(i['title'])
      title = re.sub("[,'\[\]]", "", title)
      wager = i['wagers']

      complete = f"**Title:** \n {title.title()} \n" + f"**Bet Wager:** \n {wager}"
      
      embed.add_field(name=f'Bet ID: {id}', value=f'{complete}' ,inline=True)
    await ctx.send(embed=embed)

  # Bet command function
  async def bet(self, ctx, args):
    data = self.data.read()
    args = list(args)
    if not len(args):
      await self.bet_embed(ctx, data)

    elif args[0].lower() == "create":
      args.pop(0)
      pro = {"users": [], "pool": 0}
      against = {"users": [], "pool": 0}
      await self.make_bet(ctx, args, pro, against)
      args = str(args)
      title = re.sub("[,'\[\]]", "", args)
      await ctx.send(f"Bet \"{title.title()}\" created!")

    elif args[0].lower() == "for":
      user_id = ctx.message.author.id
      args.pop(0)
      ids_dump = []
      for ids in data['ID']:
        ids_dump.append(ids)
      if user_id not in data['user_ids']:
        if args[0] in ids_dump:
          if args[1].isdigit():
            wager = args[1]
            answer = await self.check_and_spend(ctx, wager)
            if answer == 0:
              pass
          
  # Writing bet to DB
  async def make_bet(self, ctx, args, pro, against):
    data = self.data.read()
    length = len(data["bets"])
    while length in data["bets"]:
      length += 1

    wager_obj = {
      "ID": length,
      "title": args,
      "for": pro,
      "against": against,
      "user_ids": []
    }
    
    data["bets"].append(wager_obj)
    self.data.write(data)


  async def check_and_spend(self, ctx, wager):
    user_balance = self.bank.getBalance(ctx.author.id)
    # Insufficient balance
    if int(wager) >= user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} VBC')
        return
    try:
        self.bank.spendCurrency(ctx.author.id, wager)
        return 0
        
    except Exception as e:
        self.logger.warn('Failed to execute bet:')
        self.logger.warn(str(e))      

  
  async def add_to_bet(self, ctx, choice):
    pass
