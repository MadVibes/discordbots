# This handles the actual bot logic
####################################################################################################
from datetime import datetime
import configparser
import sys
import discord
import re
import math
import numpy as np


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
  async def bet_embed(self, ctx, data, json_len):
    embed = discord.Embed(
      title='Active Bets',
      description='-------',
      colour=discord.Colour.green()
    )
    if int(json_len) > 12:
      for i in data["bets"]:
        id = i['ID']
        title = str(i['title'])
        title = re.sub("[,'\[\]]", "", title)
        for_pool = i['for']['pool']
        against_pool = i['against']['pool']

        complete = f"**Title:** \n {title.title()} \n" + f"**For Pool:** \n {for_pool} VBC \n" + f"**Against Pool:** \n {against_pool} VBC"
        
        embed.add_field(name=f'Bet ID: {id}', value=f'{complete}' ,inline=True)
        
    else:
      embed.add_field(name='No Bets :(', value='What are you waiting for? Create a bet dummy!' ,inline=True)
      
    await ctx.send(embed=embed)

  # Bet command function
  async def bet(self, ctx, args):
    user_id = ctx.message.author.id
    data = self.data.read()
    args = list(args)
    if not len(args):
      json_len = len(str(data))
      await self.bet_embed(ctx, data, json_len)

    elif args[0].lower() == "create":
      args.pop(0)
      pro = {"users": [], "pool": 0}
      against = {"users": [], "pool": 0}
      await self.make_bet(ctx, args, pro, against)
      args = str(args)
      title = re.sub("[,'\[\]]", "", args)
      await ctx.send(f"Bet \"{title.title()}\" created!")

    elif args[0].lower() == "for" or args[0].lower() == "against":
      user_id = ctx.message.author.id
      choice = args[0]
      args.pop(0)
      # Get bet dictionary where IDs match
      active_bet = None
      for bet in data['bets']:
        if bet['ID'] == int(args[0]):
          active_bet = bet
          break
      # Bet doesn't exist
      if active_bet is None:
        await ctx.send("This bet doesn't exist, try again.")
        await ctx.message.add_reaction('❌')

      else:
        if user_id not in active_bet['user_ids']:
          if args[1].isdigit():
            wager = int(args[1])
            answer = await self.check_and_spend(ctx, wager)
            if answer == 1:
              userid_wager = [user_id, wager]
              if choice.lower() == "for": # Betting FOR Logic
                title = re.sub("[,'\[\]]", "", str(active_bet['title']))
                active_bet['for']['pool'] += wager
                users = active_bet['for']['users']
                active_bet['user_ids'].append(user_id)
                users.append(userid_wager)
                self.data.write(data)
                await ctx.send(f"You have bet {wager} VBC **FOR** {title}!")
                await ctx.message.add_reaction('✅')
    
              elif choice.lower() == "against": # Betting AGAINST Logic
                title = re.sub("[,'\[\]]", "", str(active_bet['title']))
                active_bet['against']['pool'] += wager
                users = active_bet['against']['users']
                active_bet['user_ids'].append(user_id)
                users.append(userid_wager)
                self.data.write(data)
                await ctx.send(f"You have bet {wager} VBC **AGAINST** {title}!")
                await ctx.message.add_reaction('✅')
        else:
          await ctx.send(f"You have bet on bet ID \"{active_bet['ID']}\" already, chill out.")
          await ctx.message.add_reaction('❌')

  # Payout function for bets
  async def pay(self, ctx, arg, arg2):
    data = self.data.read()
    active_bet = None
    for bet in data['bets']:
      if bet['ID'] == int(arg):
        active_bet = bet
        break
    if active_bet is None:
        await ctx.send("This bet doesn't exist, try again.")
        await ctx.message.add_reaction('❌')
      
    else:
      for_pool = active_bet['for']['pool']
      against_pool = active_bet['against']['pool']
      
      if arg2.lower() == "for": # FOR wins
        winners, wagers, percentages, win_amounts= [], [], [], []
        for user, wager in active_bet['for']['users']:
          winners.append(user)
          wagers.append(wager)
        for wager in wagers:
          equation = math.floor(wager / for_pool * 100)
          percentages.append(int(equation))
        for percent in percentages:
          equation = math.floor(against_pool * percent / 100)
          win_amounts.append(equation)
        final_wins = np.add(wagers, win_amounts)
        final = {winners[i]: final_wins[i] for i in range(len(winners))} 
        print(winners, wagers, percentages, win_amounts)
        print(final)
        ''' 
        for id, winnings in final.items():
        self.bank.update_balance_bet(winnings, id) # Fix with Liam
        '''
      elif arg2.lower() == "against": # AGAINST wins
        winners, wagers, percentages, win_amounts = [], [], [], []
        for user, wager in active_bet['against']['users']:
          winners.append(user)
          wagers.append(wager)
        for wager in wagers:
          equation = math.floor(wager / against_pool * 100)
          percentages.append(int(equation))
        for percent in percentages:
          equation = math.floor(for_pool * percent / 100)
          win_amounts.append(equation)
        final_wins = np.add(wagers, win_amounts)
        final = {winners[i]: final_wins[i] for i in range(len(winners))} 
        print(winners, wagers, percentages, win_amounts)
        print(final)
        '''
        for id, winnings in final.items():
          self.bank.update_balance_bet(winnings, id) # Fix with Liam
        '''
      elif arg2.lower() == "stalemate": # STALEMATE - No one wins
        for_users, against_users, for_wagers, against_wagers = [], [], [], [] 
        
        for user, wager in active_bet['for']['users']:
          for_users.append(user)
          for_wagers.append(wager)
        for user, wager in active_bet['against']['users']:
          against_users.append(user)
          against_wagers.append(wager)
          
        for_final = {for_users[i]: for_wagers[i] for i in range(len(for_users))}
        against_final = {against_users[i]: against_wagers[i] for i in range(len(against_users))}
  
        print(for_final)
        print(against_final)
      
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
        self.bank.spendCurrency(ctx.author.id, int(wager))
        return 1
        
    except Exception as e:
        self.logger.warn('Failed to execute bet:')
        self.logger.warn(str(e))      

  
  async def add_to_bet(self, ctx, choice):
    pass

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
