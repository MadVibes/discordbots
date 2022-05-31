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


  def check_tax_balance(self):
    if self.bank.get_tax_balance() >= 100:
      return True
    else:
      return False


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
    data = self.data.read()
    if data['purchaseable'] == True: # Making sure the game doesn't happen twice
      await self.toggle_purchases()
      data = self.data.read() # Reading the data again to make sure we save our changes to the next write

      channel_id = self.check_for_channel(data)
      channel_obj = await self.client.fetch_channel(channel_id)
      winning_number = random.randint(1, 100)
      if winning_number in data['taken numbers']:
        winner = self.find_winner(data, winning_number)
        await channel_obj.send(f"**The winning number is {winning_number}!** Which makes <@{winner}> our lucky winner of {data['total to win']} {self.cm.currency(animated=True)} this week!")
      else:
        await channel_obj.send(f"**The winning number is {winning_number}!** Unfortunately this time no one picked it. Good luck next week for the rollover!")
      # Reset JSON
      data['total to win'] = 0
      data['user choices'].clear()
      data['taken numbers'].clear()
      self.data.write(data)


  async def announcement(self): # Make lottery announcements
    data = self.data.read()
    channel_id = self.check_for_channel(data)
    if channel_id != 0:
      channel_obj = await self.client.fetch_channel(channel_id)

      if data['purchaseable'] == False:
        await channel_obj.send("The purchase window for lottery tickets opens in 10 minutes!") 
      
  
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
        await channel_obj.send(f"Lottery tickets are now available for purchase, the game starts in 10 minutes!\n``Price: {math.ceil(to_win / 100)}`` {self.cm.currency(animated=True)}\n``Jackpot: {to_win}`` {self.cm.currency(animated=True)}")

      else: # Toggle purchases off
        data['purchaseable'] = False
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


  # USER COMMANDS || Things that interact with the user

  async def set_posting_channel(self, ctx, id):
    data = self.data.read()
    data['posting channel'] = id
    self.data.write(data)
    await ctx.send("You have successfully updated the Lottery announcement channel!")


  async def posting_channel_choices(self, ctx): # Embed showing all text channels in the scope of ctx.guild
    channel_str = ""
    for index, channel in enumerate(ctx.guild.text_channels):
      if index < 10:
        index = f"0{str(index)}"
      channel_str += f"``{index}:`` {channel}\n"

    embed = discord.Embed(
      title='Choose a Lottery Annoucement Channel!',
      description=f'{channel_str}',
      colour=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    return {i: k.id for i, k in enumerate(ctx.guild.text_channels)}

    
  async def buy_ticket(self, ctx, number): 
    data = self.data.read()
    if data['purchaseable'] == True:
      if number not in data['taken numbers']:
        if await self.check_and_spend_lottery(ctx, int(math.ceil(data['total to win']) / 100)) == 1: # Checking user balance against the total pot / 100
          self.db_user_check(str(ctx.author.id), data)
          data['user choices'][str(ctx.author.id)].append(number)
          data['taken numbers'].append(number)
          self.data.write(data)
          await ctx.send(f"Number {number} purchased successfully!")
      else:
        await ctx.send("This number has been taken, please pick another.")
        await self.number_check(ctx)

  
  async def buy_random(self, ctx, amount): # Buy a custom amount of randomly selected tickets
    data = self.data.read()
    if data['purchaseable'] == True:
      if await self.check_and_spend_lottery(ctx, int(math.ceil(data['total to win']) / 100 * amount)) == 1:
        self.db_user_check(str(ctx.author.id), data)
        numbers_available = [i for i in range(1, 101) if i not in data['taken numbers']]
        numbers_chosen = []
        for i in range(amount):
          number = random.choice(numbers_available)
          numbers_chosen.append(number)
          data['user choices'][str(ctx.author.id)].append(number)
          data['taken numbers'].append(number)
          numbers_available.pop(numbers_available.index(number))
        self.data.write(data)

        numbers_chosen = ", ".join(str(i) for i in numbers_chosen)
        await ctx.send(f"You bought the numbers: **{numbers_chosen}**")
    

  async def number_check(self, ctx): # Embed for checking what numbers are available
    number_str = ""
    data = self.data.read()
    if data['purchaseable'] == True:
      for number in range(1, 101):
        if number < 10: # Making single digit numbers appear as a double digit in embed
          zero_placement = 0
        else:
          zero_placement = ""

        if number not in data['taken numbers']:
          number_str += f"``{zero_placement}{number}`` \u200b "

        if len(data['taken numbers']) == 100:
          number_str = "All numbers taken."

      embed = discord.Embed(
        title='Available Numbers',
        description=f'{number_str}',
        colour=discord.Color.blue()
      )
      await ctx.send(embed=embed)


  async def check_player_tickets(self, ctx): # A way for a user to check what numbers they have bought
    data = self.data.read()
    if data['purchaseable'] == True:
      if str(ctx.author.id) in data['user choices']:
        embed = discord.Embed(
          title='Your Tickets',
          description=f'{" ".join(f"``{i}``" for i in sorted(data["user choices"][str(ctx.author.id)]))}',
          colour=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
########################################################################################################
#   Copyright (C) 2022  Liam Coombs, Sam Tipper
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
