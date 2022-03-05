# This handles the actual bot logic
####################################################################################################
from datetime import datetime
import sys
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger

class Bot:

    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client
        self.guild_id = 0
    
