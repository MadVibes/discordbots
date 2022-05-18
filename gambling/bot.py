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
  "bets": [],
  "deathrolls": []
}

class Slot:
  def __init__(self):
    self.slot_machine = [[0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],
                         [0, 0, 0, 0, 0],]

  def spin(self):
    current_machine = self.slot_machine
    for row in range(len(current_machine)):
      for index, elem in enumerate(current_machine[row]):
        current_machine[row][index] = random.randint(2, 7)
    return current_machine

  def check_win(self, current_machine):
    wins = {}
    for row in range(len(current_machine)):
      multiplier = 0
      number = current_machine[row][0]
      for index, elem in enumerate(current_machine[row]):
        if current_machine[row][index] == number:
          multiplier += 1
        else:
          break
          
      if multiplier > 2:
        wins.update({row: multiplier})
    return wins


slots = Slot()

class Bot:
  def __init__(self, logger: Logger, config, bank, client: discord.Client, coin_manager: CoinManager, scratch_manager: ScratchManager):
    self.logger = logger
    self.config = config
    self.client = client
    self.bank = bank
    self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)
    self.cm = coin_manager
    self.sm = scratch_manager

  # Embed for bets
  async def bet_embed(self, ctx, data):
    embed = discord.Embed(
      title='Active Bets',
      description='-------',
      colour=discord.Colour.green()
    )
    if data['bets'] != db_schema['bets']:
      for i in data["bets"]:
        id = i['ID']
        title = str(i['title'])
        title = re.sub("[,'\[\]]", "", title) #pylint: disable=W1401
        for_pool = i['for']['pool']
        against_pool = i['against']['pool']

        complete = f"**Title:** \n {title.title()} \n" + f"**For Pool:** \n {for_pool} {self.cm.currency()} \n" + f"**Against Pool:** \n {against_pool} {self.cm.currency()}"
        
        embed.add_field(name=f'Bet ID: {id}', value=f'{complete}' ,inline=True)
        
    else:
      embed.add_field(name='No Bets :(', value='What are you waiting for? Create a bet dummy!' ,inline=True)
      
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
      ID = await self.make_bet(ctx, args, pro, against)
      args = str(args)
      title = re.sub("[,'\[\]]", "", args) #pylint: disable=W1401
      await ctx.send(f"Bet \"{title.title()}\" created, it's ID is \"{ID}\".")

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
        await self.help_embed(ctx, "bet")

      else:
        if user_id not in active_bet['user_ids']:
          if args[1].isdigit():
            wager = int(args[1])
            answer = await self.check_and_spend_bets(ctx, wager)
            if answer == 1:
              userid_wager = [user_id, wager]
              if choice.lower() == "for": # Betting FOR Logic
                title = re.sub("[,'\[\]]", "", str(active_bet['title'])) #pylint: disable=W1401
                active_bet['for']['pool'] += wager
                users = active_bet['for']['users']
                active_bet['user_ids'].append(user_id)
                users.append(userid_wager)
                self.data.write(data)
                await ctx.send(f"You have bet {wager} {self.cm.currency()} **FOR** \"{title.title()}!\"")
                await ctx.message.add_reaction('✅')
    
              elif choice.lower() == "against": # Betting AGAINST Logic
                title = re.sub("[,'\[\]]", "", str(active_bet['title'])) #pylint: disable=W1401
                active_bet['against']['pool'] += wager
                users = active_bet['against']['users']
                active_bet['user_ids'].append(user_id)
                users.append(userid_wager)
                self.data.write(data)
                await ctx.send(f"You have bet {wager} {self.cm.currency()} **AGAINST** \"{title.title()}!\"")
                await ctx.message.add_reaction('✅')
        else:
          await ctx.send(f"You have bet on bet ID \"{active_bet['ID']}\" already, chill out.")
          await ctx.message.add_reaction('❌')
          
    elif args[0].lower() == "help":
      await self.help_embed(ctx, "bet")

  # Payout function for bets
  async def pay(self, ctx, arg, arg2):
    if arg == "help":
      await self.help_embed(ctx, "pay")
      
    else:
      data = self.data.read()
      active_bet = None
      active_bet_index = None
      for j, bet in enumerate(data['bets']):
        if bet['ID'] == int(arg):
          active_bet = bet
          active_bet_index = j
          break
      if active_bet is None:
          await ctx.send("This bet doesn't exist, try again.")
          await ctx.message.add_reaction('❌')
          await self.help_embed(ctx, "pay")
        
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
        
          for id, winnings in final.items():
            self.bank.withdraw_currency_taxed(int(id), int(winnings), self.config['BET_TAX_BAND'])
          del data['bets'][active_bet_index]
          self.data.write(data)
          await self.payout_embed(ctx, active_bet, for_pool, against_pool, "for", final)
          
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
          
          for id, winnings in final.items():
            self.bank.withdraw_currency_taxed(int(id), int(winnings), self.config['BET_TAX_BAND'])
          del data['bets'][active_bet_index]
          self.data.write(data)
          await self.payout_embed(ctx, active_bet, for_pool, against_pool, "against", final)
          
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
  
          for id, winnings in for_final.items():
            self.bank.withdraw_currency_taxed(int(id), int(winnings), self.config['BET_TAX_BAND'])
          for id, winnings in against_final.items():
            self.bank.withdraw_currency_taxed(int(id), int(winnings), self.config['BET_TAX_BAND'])
          del data['bets'][active_bet_index]
          self.data.write(data)
          await self.payout_embed(ctx, active_bet, for_pool, against_pool, "stalemate", for_final, against_final)

  # Payout Embed
  async def payout_embed(self, ctx, active_bet, for_pool, against_pool, result, final1, final2=None):
    if result == "for":
      title = "For Wins!"
      colour = discord.Colour.green()
    elif result == "against":
      title = "Against Wins!"
      colour = discord.Colour.red()
    elif result == "stalemate":
      title = "Stalemate!"
      colour = discord.Colour.gold()
    active_bet = re.sub("[,'\[\]]", "", str(active_bet['title'])) #pylint: disable=W1401
    active_bet = active_bet.title()
    
    embed = discord.Embed(
      title=f'{title}',
      description=f'**Bet Title:** {active_bet}',
      colour=colour
    )
    
    for id, winnings in final1.items():
      user_obj = await self.client.fetch_user(int(id))
      embed.add_field(name=f'{user_obj}:', value=f'+{winnings} {self.cm.currency()} ᵇᵉᶠᵒʳᵉ ᵗᵃˣ' ,inline=False)

    if final2 != None:
      for id, winnings in final2.items():
        user_obj = await self.client.fetch_user(int(id))
        embed.add_field(name=f'{user_obj}:', value=f'+{winnings} {self.cm.currency()} ᵇᵉᶠᵒʳᵉ ᵗᵃˣ' ,inline=False)

    embed.add_field(name='For Pool Total:', value=f'{for_pool} {self.cm.currency()}' ,inline=True)
    embed.add_field(name='Against Pool Total:', value=f'{against_pool} {self.cm.currency()}' ,inline=True)
        
    await ctx.send(embed=embed)

  # Help emebeds for bot
  async def help_embed(self, ctx, type):
    if type == "bet":
      title = "Bet Command Help"
  
    elif type == "pay":
      title = "Pay Command Help"

    elif type == "deathroll":
      title = "Deathroll Command Help"

    elif type == "scratchcard":
      title = "Scratchcard Command Help"

    elif type == "slots":
      title = "Slots Command Help"
      
    embed = discord.Embed(
      title=f'{title}',
      colour=discord.Colour.green()
    )
    
    if type == "bet":
      embed.add_field(name='$bet', value='Displays all active bets.' ,inline=False)
      embed.add_field(name='$bet create [name]', value='Creates a bet with a custom name and gives it a unique ID used in the commands listed below.' ,inline=False)
      embed.add_field(name='$bet for [ID] [wager]', value='Adds your wager to the **FOR** pool. ' ,inline=False)
      embed.add_field(name='$bet against [ID] [wager]', value='Adds your wager to the **AGAINST** pool. ' ,inline=False)
      
    elif type == "pay":
      embed.add_field(name='$pay [ID] [for | against | stalemate]', value='Use this command to pay the winner(s) of a bet. If the against team won, it would look something like this \"($pay [ID] [against])\".' ,inline=False)

    elif type == "deathroll":
      embed.add_field(name='$deathroll', value='Shows all active deathrolls.' ,inline=False)
      embed.add_field(name='$deathroll create [wager]', value='Creates a deathroll game with a custom wager and unique ID.' ,inline=False)
      embed.add_field(name='$deathroll join [ID]', value='Joins a deathroll game.' ,inline=False)
      embed.add_field(name='$deathroll start [ID]', value='Starts the deathroll game, can only be used by the game\'s initiator.' ,inline=False)
      embed.add_field(name='$deathroll delete [ID]', value='Deletes a deathroll game , can only be used by the game\'s initiator.' ,inline=False)

    elif type == "scratchcard":
      embed.add_field(name='$scratchcard buy [Amount]', value='Starts a scratchcard for the amount specified', inline=False)

    elif type == "slots":
      embed.add_field(name='$slots spin [wager]', value='Spin the slot machine with a custom wager.' ,inline=False)

    await ctx.send(embed=embed)
    
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
    return length


  async def check_and_spend_bets(self, ctx, wager):
    user_balance = self.bank.get_balance(ctx.author.id)
    # Insufficient balance
    if int(wager) > user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} {self.cm.currency()}')
        return
    try:
        self.bank.spend_currency_taxed(ctx.author.id, int(wager), self.config['BET_TAX_BAND'])
        return 1
        
    except Exception as e:
        self.logger.warn('Failed to execute bet:')
        self.logger.warn(str(e))      

  async def check_and_spend_deathroll(self, ctx, wager):
    user_balance = self.bank.get_balance(ctx.author.id)
    # Insufficient balance
    if int(wager) > user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} {self.cm.currency()}')
        return
    try:
        self.bank.spend_currency_taxed(ctx.author.id, int(wager), self.config['DEATHROLL_TAX_BAND'])
        return 1
        
    except Exception as e:
        self.logger.warn('Failed to execute bet:')
        self.logger.warn(str(e))    

#############################################################################################
# Deathrolling
#############################################################################################

  # Active deathroll embed
  async def deathroll_embed(self, ctx, data):
    embed = discord.Embed(
      title='Active Deathrolls',
      description='-------',
      colour=discord.Colour.green()
    )
    if data['deathrolls'] != db_schema['deathrolls']:
      for i in data["deathrolls"]:
        ID = i['ID']
        wager = str(i['wager'])
        winnings = int(wager) * 2
        player_1 = i['competitors'][0]
        player_1_obj = await self.client.fetch_user(player_1)
        if len(i['competitors']) == 2:
          player_2 = i['competitors'][1]
          player_2_obj = await self.client.fetch_user(player_2)
          ready = "**Ready to start!**"
        else:
          player_2_obj = None
          ready = ""
          
        complete = f"**Wager:** \n {wager} {self.cm.currency()} \n" + f"**Amount to win:** \n {winnings} {self.cm.currency()} \n" + f"**Initiator / Player 1:** \n {player_1_obj} \n" + f"**Player 2:** \n {player_2_obj} \n" + f"{ready}"

        
        embed.add_field(name=f'Deathroll ID: {ID}', value=f'{complete}' ,inline=True)
        
    else:
      embed.add_field(name='No Deathrolls :(', value='What are you waiting for? Create a game of deathroll dummy!' ,inline=True)
      
    await ctx.send(embed=embed)
    
  # Creates a deathroll game
  async def create_dr(self, ctx, wager, initiator, data):
    answer = await self.check_and_spend_deathroll(ctx, wager)
    if answer == 1:
      length = len(data["deathrolls"])
      while length in data["deathrolls"]:
        length += 1

      deathroll_data = {
        "ID": length,
        "wager": wager,
        "initiator": initiator,
        "competitors": [initiator]
      }

      data["deathrolls"].append(deathroll_data)
      self.data.write(data)
      return length

  # Deathroll game starts
  async def deathroll_game(self, ctx, wager, player1, player2, data, active_bet_index):
    wager1, wager2 = int(wager), int(wager)
    turn = 0
    while wager1 != 1:
      if turn == 0:
        if wager1 > 10:
          wager1 = max(random.randint(1, wager1), random.randint(1, wager1))
        else:
          wager1 = random.randint(1, wager1)
        await ctx.send(f"<@{player1}> rolled a {wager1}!")
        if wager1 != 1:
          turn = 1
          await asyncio.sleep(1)
        
      elif turn == 1:
        if wager1 > 10:
          wager1 = max(random.randint(1, wager1), random.randint(1, wager1))
        else:
          wager1 = random.randint(1, wager1)
        await ctx.send(f"<@{player2}> rolled a {wager1}!")
        if wager1 != 1:
          turn = 0
          await asyncio.sleep(1)

    wager2 *= 2
    if turn == 1: # Player 1 wins
      self.bank.withdraw_currency_taxed(int(player1), int(wager2), self.config['DEATHROLL_TAX_BAND'])
      del data['deathrolls'][active_bet_index]
      self.data.write(data)
      await ctx.send(f"<@{player1}> wins {wager2} {self.cm.currency()}!")
      
    elif turn == 0: # Player 2 wins
      self.bank.withdraw_currency_taxed(int(player2), int(wager2), self.config['DEATHROLL_TAX_BAND'])
      del data['deathrolls'][active_bet_index]
      self.data.write(data)
      await ctx.send(f"<@{player2}> wins {wager2} {self.cm.currency()}!")

  # Deathroll prep before game
  async def prep_deathroll(self, ctx, data, arg2, user):
    active_bet = None
    active_bet_index = None
    for j, bet in enumerate(data['deathrolls']):
      if bet['ID'] == int(arg2):
        active_bet = bet
        active_bet_index = j
        break
    
    if active_bet == None:
      await ctx.message.add_reaction('❌')
      await ctx.send(f"No deathroll game found with the id of \"{arg2}\", please try again.")

    else:
      if int(user) == active_bet['initiator']:
        wager = active_bet["wager"]
        if len(active_bet["competitors"]) == 2:
          player1 = int(active_bet["competitors"][0])
          player2 = int(active_bet["competitors"][1])
          await ctx.send(f"The deathroll will begin in 5 seconds, good luck to <@{player1}> & <@{player2}>!")
          await asyncio.sleep(5)
          
          await self.deathroll_game(ctx, wager, player1, player2, data, active_bet_index)
  
        else:
          await ctx.message.add_reaction('❌')
          await ctx.send("This deathroll doesn't have two players yet, come back when someone accepts your challenge")
        
      else: 
        await ctx.message.add_reaction('❌')
        await ctx.send(f"<@{user}>, if you didn't initiate the deathroll, you can't start it.")

  # Deathroll main command
  async def deathroll(self, ctx, arg, arg2):
    data = self.data.read()
    if arg == None:
      await self.deathroll_embed(ctx, data)

    else:
      user = ctx.message.author.id
      
      if arg.lower() == "create":
        if arg2 != None:
          if arg2.isdigit():
            if int(arg2) > 1:
              ID = await self.create_dr(ctx, int(arg2), int(user), data)
              if ID != None:
                await ctx.message.add_reaction('✅')
                await ctx.send(f"Deathroll created, it's ID is \"{ID}\".")
            
            else:
              await ctx.message.add_reaction('❌')
              await ctx.send(f"The wager must be more than 1 {self.cm.currency()} dummy.")
        else:
          await ctx.message.add_reaction('❌')
          await ctx.send("2nd argument missing \"$deathroll create [wager]\".")
          
      elif arg.lower() == "join":
        active_bet = None
        if arg2 != None:
          for bet in data['deathrolls']:
            if bet['ID'] == int(arg2):
              active_bet = bet
              break
  
          if active_bet == None:
            await ctx.message.add_reaction('❌')
            await ctx.send(f"No deathroll game found with the id of \"{arg2}\", please try again.")
            
          else:
            competitors = active_bet['competitors']
            if len(competitors) < 2:
              wager = active_bet['wager']
              answer = await self.check_and_spend_deathroll(ctx, wager)
              if answer == 1:
                competitors.append(int(user))
                self.data.write(data)
                await ctx.message.add_reaction('✅')
                await ctx.send(f"You have spent {wager} {self.cm.currency()} and joined the deathroll! The initator can start it when you are both ready.")
            else:
              await ctx.message.add_reaction('❌')
              await ctx.send("This deathroll already has two players... Sorry :(")
        else:
          await ctx.message.add_reaction('❌')
          await ctx.send("2nd argument missing \"$deathroll join [ID]\".")
          
      elif arg.lower() == "start":
        if arg2 != None:
          await self.prep_deathroll(ctx, data, arg2, user)
        else:
          await ctx.message.add_reaction('❌')
          await ctx.send("2nd argument missing \"$deathroll start [ID]\".")

      elif arg.lower() == "delete":
        if arg2 != None:
          active_bet = None
          active_bet_index = None
          for j, bet in enumerate(data['deathrolls']):
            if bet['ID'] == int(arg2):
              active_bet = bet
              active_bet_index = j
              break
  
          if active_bet == None:
            await ctx.message.add_reaction('❌')
            await ctx.send(f"No deathroll game found with the ID of \"{arg2}\", please try again.")
          else:
            if int(user) == active_bet['initiator']:
              competitors = active_bet['competitors']
              wager = active_bet['wager']
              player1 = competitors[0]
              self.bank.withdraw_currency_taxed(int(player1), int(wager), self.config['DEATHROLL_TAX_BAND'])
              if len(competitors) == 2:
                player2 = competitors[1]
                self.bank.withdraw_currency_taxed(int(player2), int(wager), self.config['DEATHROLL_TAX_BAND'])
              del data['deathrolls'][active_bet_index]
              self.data.write(data)
              await ctx.message.add_reaction('✅')
              await ctx.send(f"Successfully deleted deathroll ID \"{active_bet_index}\" and refunded all players.")
              
            else:
              await ctx.message.add_reaction('❌')
              await ctx.send("You can't delete deathrolls that you didn't initiate.")
              
        else:
          await ctx.message.add_reaction('❌')
          await ctx.send("2nd argument missing \"$deathroll delete [ID]\".")
            
      elif arg.lower() == "help":
        await self.help_embed(ctx, "deathroll")


#############################################################################################
# Scratch cards
#############################################################################################


  async def check_and_spend_scratchcard(self, ctx, amount):
    """Making sure user has enough money to purchase card"""
    user_balance = self.bank.get_balance(ctx.author.id)
    # Insufficient balance
    if int(amount) > user_balance:
      await ctx.reply(f'Insufficient balance, current balance is {user_balance} {self.cm.currency()}') # If balance insf
      return
    try:
      self.bank.spend_currency_taxed(ctx.author.id, int(amount), self.config['SCRATCHCARD_TAX_BAND']) # Spending the amount
      return 1

    except Exception as e:
      self.logger.warn('Failed to execute bet:')
      self.logger.warn(str(e))


  async def purchase_card(self, ctx, amount, user):
    """Handling purchase of a scratch card"""
    ans = await self.check_and_spend_scratchcard(ctx, amount)
    if ans == 1:
      return 1


  def get_multiplier(self):
    """Multiplier calculation for winnings"""
    rand = random.randint(1, 100)
    multiplier = 2 + (math.pow((93 / 100), ((0 - rand) + 65)))
    return multiplier


  def get_scratch_card(self):
    """
    Generates a card
    returns 2 vars, win (bool) and card (nested array/matrix)
    """
    chance_to_win = 18  # In percentage
    chance_to_almost = 20 # In Percentage
    emojis = self.sm.get_scratch_emojis()
    def almost():
      left_align = True if (randint(0, 1) == 0) else False
      _emojis = emojis.copy()
      almost_emoji = _emojis.pop(randint(0, len(_emojis) - 1))
      if left_align:
        return [almost_emoji, almost_emoji, _emojis[randint(0, len(_emojis) - 1)]]
      else:
        return [_emojis[randint(0, len(_emojis)) - 1], almost_emoji, almost_emoji]

    def winning():
      random_emoji = emojis[randint(0, len(emojis)) - 1]
      return [random_emoji, random_emoji, random_emoji]

    def random():
      row = []
      _emojis = emojis.copy()
      for i in range(3): #pylint: disable=w0612
        row.append(_emojis.pop(randint(0, len(_emojis) - 1)))
      return row

    win = (randint(0, 100) <= chance_to_win)
    card = [
      random() if randint(0, 100) > chance_to_almost else almost(),
      winning() if win == True else (random() if randint(0, 100) > chance_to_almost else almost()),
      random() if randint(0, 100) > chance_to_almost else almost()
    ]
    shuffle(card)
    return win, card


  def convert_card_to_string(self, card):
    """Converts card matrix to string for discord"""
    d_string = ''
    for row in card:
      d_string += '`|    \/    | `'+ '`-`'.join(row) +'` |    \/    |`' #pylint: disable=w1401
      d_string += '\n'
    return d_string


  # Function of the actual game
  async def scratch_card_game(self, ctx, amount, user):
    """Actual scratch card game"""
    padding_amount = 26
    win, card = self.get_scratch_card()
    multiplier = self.get_multiplier()

    pretty_multiplier = "{:.2f}".format(multiplier)
    winning_amount = math.floor(amount * multiplier)  # Using the predefined math equation to give multipier
    pretty_string_winning_amount = f'{amount} x {pretty_multiplier} -> {winning_amount}'

    blank = (' ' * len(str(pretty_string_winning_amount)))
    padding = (' ' * (padding_amount - len(str(pretty_string_winning_amount))))

    outcome = f'||`| You won! {pretty_string_winning_amount}{padding}|`||' if win else f'||`| You lost...{blank}{padding[:-2]}|`||'
    if win:
      await ctx.send(self.convert_card_to_string(card) + outcome)
      self.bank.summon_currency(user, winning_amount) # Winning scratchcard
    else:
      await ctx.send(self.convert_card_to_string(card) + outcome)


  async def scratchcard(self, ctx, arg, arg2):
    """Main scratch card command"""
    user = ctx.author.id
    if (arg != None
        and arg.lower() == "buy" # Initiator command
        and arg2 != None
        and arg2.isdigit()
        and int(arg2) >= int(self.config['SCRATCHCARD_MIN_BET'])):
      amount = int(arg2)
      ans = await self.purchase_card(ctx, amount, user)  # Purchasing and withdrawing amount from their balance
      if ans == 1:
        await self.scratch_card_game(ctx, amount, user)  # Starting the scratchcard
        await ctx.message.add_reaction('✅')

    elif arg.lower() == "help": # Help embed
      await self.help_embed(ctx, "scratchcard")

    else:
      await ctx.message.add_reaction('❌')
      await ctx.send(f'$scratchcard buy [amount]\nYou need to wager atleast {self.config["SCRATCHCARD_MIN_BET"]} {self.cm.currency()}!')


#############################################################################################
# Slots
#############################################################################################

  async def check_and_spend_slots(self, ctx, amount):
      """Making sure user has enough money to play on the slot machine"""
      user_balance = self.bank.get_balance(ctx.author.id)
      # Insufficient balance
      if int(amount) > user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} {self.cm.currency()}') # If balance insf
        return
      try:
        self.bank.spend_currency_taxed(ctx.author.id, int(amount), self.config['SLOTS_TAX_BAND']) # Spending the amount
        return 1

      except Exception as e:
        self.logger.warn('Failed to execute bet:')
        self.logger.warn(str(e))


  async def slots(self, ctx, wager):
    answer = await self.check_and_spend_slots(ctx, wager)

    if answer == 1:
      await ctx.message.add_reaction('✅')
      current_slots = slots.spin()
      wins = slots.check_win(current_slots)
      win_amount = 0
      slot_str = "O\n"

      
      for row in range(len(current_slots)):
        if row in wins:
          slot_str += f"|\| \u200b \u200b >> **|{str(current_slots[row]).replace(',', '').strip()}|** << Win x{(wins[row])*2}!\n"
          win_amount += wins[row]*2 * wager
        else:
          slot_str += f"|\| \u200b \u200b >> **|{str(current_slots[row]).replace(',', '').strip()}|** <<\n"
          
      if wins:
        slot_str += f"\nYou won {win_amount}!"
        self.bank.summon_currency(ctx.author.id, win_amount)
      else:
        slot_str += f"\nYou lost..."
        
      embed = discord.Embed(
        title='Slot Machine',
        description = slot_str,
        colour=discord.Colour.gold()
      )
      await ctx.send(embed=embed)
    else:
      await ctx.message.add_reaction('❌')

  

########################################################################################################
#   Copyright (C) 2022  Liam Coombs, Sam Tipper, Rhydian Davies
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