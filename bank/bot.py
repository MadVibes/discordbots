# This handles the actual bot logic
####################################################################################################
from datetime import datetime
import sys
import configparser
import discord

sys.path.insert(0, '../')
from lib.data import Database
from lib.logger import Logger

class Bot:

    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client

        db_schema = {
            'users': []
        }

        self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)
    
    def user_id_exists(self, user_id: int):
        """Does user name exist"""
        data = self.data.read()
        for user in data['users']:
            if user['user_id'] == user_id:
                return True
        return False

    def create_user(self, user_id: int, user_name: str):
        """Create a new user, returns true|false if success"""
        data = self.data.read()
        if user_name in data['users']:
            self.logger.warn(f'Attempted to create user "{user_name}" but they already exist')
            return False
        else:
            user_schema = {
                'user_id': int(user_id),
                'created_time': str(datetime.now().strftime("%s")),# In epoch time
                'balance': 0,
                'meta': []
            }

            data['users'].append(user_schema)
            self.data.write(data)
            return True
