# This handles the actual bot logic
####################################################################################################
import sys
import discord
import re
import math
import numpy as np
import asyncio
import random
from random import randint, shuffle

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.data import Database #pylint: disable=E0401
from lib.bank_interface import Bank #pylint: disable=E0401
from lib.emote_manager import CoinManager, ScratchManager #pylint: disable=E0401


db_schema = {
  "user choices": {}, 
  "taken numbers": [],
  "purchaseable": False,
  "lottery completed": False,
  "total to win": 0,
  "posting channel": 0
}


class Bot:
  def __init__(self, logger: Logger, config, bank, client: discord.Client, coin_manager: CoinManager, scratch_manager: ScratchManager):
    self.logger = logger
    self.config = config
    self.client = client
    self.bank = bank
    self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)
    self.cm = coin_manager
    self.sm = scratch_manager


  def find_random_channel(self):
    for guild in self.client.guilds:
      if str(guild) == self.config['DISCORD_GUILD']:
        channel = random.choice(guild.text_channels).id
        break
          
      else:
        channel = 0

    return channel


  def check_for_channel(self, data=False): 
    if data == False: # If data has already been read, we don't want to do it again
      data = self.data.read()

    if data['posting channel'] == 0: # If channel isn't specified, obtain a random one from the same server/guild
      channel_id = self.find_random_channel() 
    else: 
      channel_id = data['posting channel']

    return channel_id


  async def announcement(self): # Make lottery announcements
    data = self.data.read()
    channel_id = self.check_for_channel(data=data)
    if channel_id != 0:
      channel_obj = await self.client.fetch_channel(channel_id)

      if data['purchaseable'] == False:
        await channel_obj.send("The purchase window for lottery tickets opens in 1 hour!") 
      
  
  async def open_purchases(self): # Opening ticket purchases
    data = self.data.read()
    channel_id = self.check_for_channel(data=data)

    if channel_id != 0:
      to_win = self.bank.get_tax_balance()
      data['purchaseable'] = True
      data['total to win'] = to_win
      self.data.write(data)
      channel_obj = await self.client.fetch_channel(channel_id)
      await channel_obj.send(f"Lottery tickets are now available for purchase!\n``Price: {math.floor(to_win / 100)}`` {self.cm.currency(animated=True)}\n``Jackpot: {to_win}`` {self.cm.currency(animated=True)}")

  
  async def check_and_spend_lottery(self, ctx, amount):
      """Making sure user has enough money to buy a lottery ticket"""
      user_balance = self.bank.get_balance(ctx.author.id)
      # Insufficient balance
      if int(amount) > user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} {self.cm.currency()}') # If balance insf
        return
      try:
        self.bank.spend_currency_taxed(ctx.author.id, int(amount), self.config['LOTTERY_TAX_BAND']) # Spending the amount
        return 1

      except Exception as e:
        self.logger.warn('Failed to execute bet:')
        self.logger.warn(str(e))


  def db_user_check(self, user, data):
    if user not in data['user choices']:
      user_schema = {user: []}
      self.data.write(user_schema)


  # USER COMMANDS

  async def buy_ticket(self, ctx, number):
    data = self.data.read()
    if data['purchaseable'] == True:
      if number not in data['taken numbers']:
        if await self.check_and_spend_lottery(ctx, int(math.floor(data['total to win']) / 100)) == 1:
          self.db_user_check(ctx.author.id, data)
          #data['user choices'][ctx.author.id]
      

