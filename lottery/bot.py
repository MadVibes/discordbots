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


db_schema = {
  "user choices": {}, 
  "taken numbers": [],
  "purchaseable": False,
  "lottery completed": False,
  "posting channel": 0
}


class Bot:
  def __init__(self, logger: Logger, config, bank, client: discord.Client):
    self.logger = logger
    self.config = config
    self.client = client
    self.bank = bank
    self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)


  def find_random_channel(self):
    for guild in self.client.guilds:
      if str(guild) == self.config['DISCORD_GUILD']:
        channel = random.choice(guild.text_channels).id
        break
          
      else:
        channel = 0

    return channel


  async def announcement(self):
    data = self.data.read()
    if data['posting channel'] == 0: # If channel isn't specified, obtain a random one from the same server/guild
      channel_id = self.find_random_channel() 
    else: 
      channel_id = data['posting channel']
      
    if channel_id != 0:
      channel_obj = await self.client.fetch_channel(channel_id)
      await channel_obj.send("Pog!") 
      
    
      
      