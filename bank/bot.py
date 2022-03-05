# This handles the actual bot logic
####################################################################################################
from datetime import datetime
from re import A
import sys, json
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.data import Database
from lib.logger import Logger

class Bot:

    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client
        self.guild_id = 0

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

    def alter_balance(self, amount: int, user_id: int):
        """Alter balance by amount"""
        data = self.data.read()
        for user in data['users']:
            if user['user_id'] == user_id:
                user['balance'] += amount

        self.data.write(data)

    def handle_input(self, json_in):
        """Handle action"""
        action = json_in['action']

        if action == 'getBalance':
            # Validate required parameters
            if ('parameters' not in json_in 
                or 'user_id' not in json_in['parameters']):
                self.logger.warn('Request for getBalance is missing parameters')
                return {
                    'request': 'failure',
                    'message': 'missing parameters, parameters: user_id are required'
                }

            return self.req_get_balance(json_in['parameters']['user_id'])

    def req_get_balance(self, user_id):
        """Handle request to get balance and create response"""
        data = self.data.read()
        balance = -1
        for user in data['users']:
            if user['user_id'] == user_id:
                balance = user['balance']

        response = {}
        if balance != -1:
            response = {
                'request': 'success',
                'balance': balance
            }
        else:
            response = {
                'request': 'failure',
                'message': 'user_id does not exist',
                'balance': balance
            }

        return response