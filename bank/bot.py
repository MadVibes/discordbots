# This handles the actual bot logic
####################################################################################################
import sys
import configparser
import discord

sys.path.insert(0, '../')
from lib.data import Database



class Bot:

    def __init__(self, logger, config, client):
        self.logger = logger
        self.config = config
        self.client = client

        self.data = Database(self.logger, self.config['DATA_STORE'])
