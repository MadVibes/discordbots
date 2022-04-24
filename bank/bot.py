# This handles the actual bot logic
####################################################################################################
from datetime import datetime
import sys, json, re
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.data import Database #pylint: disable=E0401
from lib.logger import Logger #pylint: disable=E0401

class Bot:


    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client
        self.guild_id = 0

        # Init database
        db_schema = {
            'users': []
        }

        self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)

        # Create tax bands from configs
        config_dict = {k:v for k, v in self.config.items()}
        tax_bands_config = list(filter(lambda conf: re.match('^TAX_BAND_', str(conf).upper()), config_dict.keys()))
        tax_bands = {}
        for band in tax_bands_config:
            if band in config_dict.keys():
                tax_bands[band.replace("tax_band_", "", 1)] = config_dict[band]
        self.tax_bands = tax_bands


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
        balance = 0
        for user in data['users']:
            if user['user_id'] == user_id:
                user['balance'] += amount
                balance = user['balance']
        self.data.write(data)
        return balance


    def get_balance(self, user_id: int):
        """Get the balance of a user id"""
        if not(self.user_id_exists(user_id)):
            self.create_user(user_id, str(user_id))

        data = self.data.read()
        balance = -1
        for user in data['users']:
            if user['user_id'] == user_id:
                balance = user['balance']
        return balance


    def handle_input(self, json_in):
        """Handle action"""
        action = json_in['action']

        if action == 'getBalance':
            # Validate required parameters
            if ('parameters' not in json_in
                or 'user_id' not in json_in['parameters']):
                self.logger.warn('Request for getBalance is missing parameters')
                return {
                    'request': 'Failure',
                    'message': 'missing parameters, parameters: user_id are required'
                }

            return self.req_get_balance(json_in['parameters']['user_id'])

        if action == 'moveCurrency':
            # Validate required parameters
            if ('parameters' not in json_in
                or 'user_id_sender' not in json_in['parameters']
                or 'user_id_receiver' not in json_in['parameters']):
                self.logger.warn('Request for getBalance is missing parameters')
                return {
                    'request': 'Failure',
                    'message': 'missing parameters, parameters: user_id_sender and user_id_receiver are required'
                }

            return self.req_get_balance(json_in['parameters']['user_id'])


    def req_get_balance(self, user_id):
        """Handle request to get balance and create response"""
        balance = self.get_balance(user_id)

        response = {}
        if balance != -1:
            response = {
                'request': 'Success',
                'balance': balance
            }
        else:
            # Currently, the get_balance function will create a missing user. So this should never happen
            response = {
                'request': 'Failure',
                'message': 'user_id does not exist',
                'balance': balance
            }

        return response


    def req_move_currency(self, user_id_sender, user_id_receiver, amount):
        """Handle request to move currency and create response"""
        sender_balance = self.get_balance(user_id_sender)
        receiver_balance = self.get_balance(user_id_receiver)

        # If target isers dont exist
        if sender_balance==-1 or receiver_balance ==-1:
            sender = ('exists' if sender_balance!=-1 else 'missing')
            receiver = ('exists' if receiver_balance!=-1 else 'missing')
            return {
                'request': 'Failure',
                'message': 'either sender or receiver user does not exist',
                'sender': sender,
                'receiver': receiver
            }

        # Sender has insufficient funds
        if sender_balance < amount:
            return {
                'request': 'Failure',
                'message': 'user_id_sender has insufficient balance',
                'balance': sender_balance
            }

        # Try move balance
        try:
            sender_balance = self.alter_balance(-amount, user_id_sender)
            receiver_balance = self.alter_balance(amount, user_id_receiver)
            self.logger.log(f'Transferred {user_id_sender} -> {user_id_receiver} ({amount})')
            return {
                'request': 'Success',
                'message': 'balance transferred',
                'balance_sender': sender_balance,
                'balance_receiver': receiver_balance
                }
        # Handle error
        except Exception as e:
            self.logger.warn('Failed to move currency:' + str(e))
            self.logger.warn(f'{user_id_sender} -> {user_id_receiver} ({amount})')
            return {
                'request': 'Failure',
                'message': str(e)
            }


    def req_summon_currency(self, user_id_receiver, amount):
        """
        Handle request to summon currency and create response
        NOTE: This is creating NEW currency out of thin air.
        """
        receiver_balance = self.get_balance(user_id_receiver)

        # Try move balance
        try:
            receiver_balance = self.alter_balance(amount, user_id_receiver)
            self.logger.log(f'Summoned -> {user_id_receiver} ({amount})')
            return {
                'request': 'Success',
                'message': 'balance increased',
                'balance_receiver': receiver_balance
                }
        # Handle error
        except Exception as e:
            self.logger.warn('Failed to summon currency:' + str(e))
            self.logger.warn(f'Summon -> {user_id_receiver} ({amount})')
            return {
                'request': 'Failure',
                'message': str(e)
            }


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
