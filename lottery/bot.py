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


  def check_for_channel(self, data): 
    if data['posting channel'] == 0: # If channel isn't specified, obtain a random one from the same server/guild
      channel_id = self.find_random_channel() 
    else: 
      channel_id = data['posting channel']

    return channel_id


  def find_winner(self, data, winning_number):
    for id, numbers in data['user choices'].items():
      if winning_number in numbers:
        break
    
    self.bank.withdraw_tax_currency(int(id), data['total to win'])
    
    return id


  async def lottery_game(self): # The actual game
    await self.toggle_purchases()
    data = self.data.read()
    channel_id = self.check_for_channel(data)
    channel_obj = await self.client.fetch_channel(channel_id)
    winning_number = random.randint(1, 100)
    if winning_number in data['taken numbers']:
      winner = await self.find_winner(data, winning_number)
      await channel_obj.send(f"**The winning number is {winning_number}!** Which makes <@{winner}> our lucky winner of {data['total to win']} this week!")
    else:
      await channel_obj.send(f"**The winning number is {winning_number}!** Unfortunately this time no one picked it. Good luck next week for the rollover!")


  async def announcement(self): # Make lottery announcements
    data = self.data.read()
    channel_id = self.check_for_channel(data)
    if channel_id != 0:
      channel_obj = await self.client.fetch_channel(channel_id)

      if data['purchaseable'] == False:
        await channel_obj.send("The purchase window for lottery tickets opens in 1 hour!") 
      
  
  async def toggle_purchases(self): # Toggle ticket purchases on/off
    data = self.data.read()
    channel_id = self.check_for_channel(data)

    if channel_id != 0:
      to_win = self.bank.get_tax_balance()
      if data['purchaseable'] == False: # Toggle purchasing on
        data['purchaseable'] = True
        data['total to win'] = to_win
        self.data.write(data)
        channel_obj = await self.client.fetch_channel(channel_id)
        await channel_obj.send(f"Lottery tickets are now available for purchase!\n``Price: {math.floor(to_win / 100)}`` {self.cm.currency(animated=True)}\n``Jackpot: {to_win}`` {self.cm.currency(animated=True)}")

      else: # Clear JSON when the game decides the winner
        data['purchaseable'] = False
        data['total to win'] = 0
        data['user choices'].clear()
        data['taken numbers'].clear()
        self.data.write(data)
      

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
      data['user choices'].update({user: []})
      self.data.write(data)


  # USER COMMANDS

  async def buy_ticket(self, ctx, number):
    data = self.data.read()
    if data['purchaseable'] == True:
      if number not in data['taken numbers']:
        if await self.check_and_spend_lottery(ctx, int(math.floor(data['total to win']) / 100)) == 1: # Checking user balance against the total pot / 100
          self.db_user_check(str(ctx.author.id), data)
          data['user choices'][str(ctx.author.id)].append(number)
          data['taken numbers'].append(number)
          self.data.write(data)
          await ctx.send(f"Number {number} purchased successfully!")
      else:
        await ctx.send("This number has been taken, please pick another.")
        await self.number_check(ctx)

  
  async def buy_random(self, ctx, amount):
    data = self.data.read()
    if data['purchaseable'] == True:
      if await self.check_and_spend_lottery(ctx, int(math.floor(data['total to win']) / 100 * amount)) == 1:
        self.db_user_check(str(ctx.author.id), data)
        numbers_available = [i for i in range(1, 101) if i not in data['taken numbers']]
        numbers_chosen = []
        for i in range(amount):
          number = random.choice(numbers_available)
          numbers_chosen.append(number)
          data['user choices'][str(ctx.author.id)].append(number)
        self.data.write(data)

        numbers_chosen = ", ".join(str(i) for i in numbers_chosen)
        await ctx.send(f"You bought the numbers: **{numbers_chosen}**")
    

  async def number_check(self, ctx):
    number_str = ""
    data = self.data.read()
    for number in range(1, 101):
      if number < 10: # Making single digit numbers appear as a double digit in embed
        zero_placement = 0
      else:
        zero_placement = ""

      if number in data['taken numbers']:
        number_str += f"~~``{zero_placement}{number}``~~ \u200b "
      else:
        number_str += f"``{zero_placement}{str(number)}`` \u200b "

    embed = discord.Embed(
      title='Available Numbers',
      description=f'{number_str}',
      colour=discord.Color.blue()
    )
    await ctx.send(embed=embed)
      

