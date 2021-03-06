# Bank interface
# Handles interfacing with the bank bot udner the hood to make lazy devs time easier sending HTTP requests
###########################################################################################################
import requests, sys
from json import dumps, loads

sys.path.insert(0, '../')
from lib.logger import Logger #pylint: disable=E0401

class Bank:


    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.default_headers = {
            'Content-Type': 'application/json'
        }


    def get_balance(self, user_id: int):
        """Get users balance using user_id. Returns user balance as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'getBalance',
            'parameters': {
                'user_id': user_id
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance'])


    def get_bank_balance(self):
        """Get bank balance. Returns bank balance as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'getBankBalance',
            'parameters': {}
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance'])


    def get_tax_balance(self):
        """Get tax balance. Returns tax balance as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'getTaxBalance',
            'parameters': {}
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance'])


    def move_currency(self, user_id_sender: int, user_id_receiver: int, amount: int):
        """Moves balance from one user id to another. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'moveCurrency',
            'parameters': {
                'user_id_sender': user_id_sender,
                'user_id_receiver': user_id_receiver,
                'amount': amount
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response'])


    def move_currency_taxed(self, user_id_sender: int, user_id_receiver: int, amount: int, tax_band: str):
        """Moves balance from one user id to another with tax. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'moveCurrencyTaxed',
            'parameters': {
                'user_id_sender': user_id_sender,
                'user_id_receiver': user_id_receiver,
                'amount': amount,
                'tax_band': tax_band
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response'])


    def spend_currency(self, user_id: int, amount: int):
        """Spend users balance using user_id. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'spendCurrency',
            'parameters': {
                'user_id': user_id,
                'amount': amount
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance_sender'])


    def withdraw_currency(self, user_id: int, amount: int):
        """Withdraw from bank to users balance using user_id. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'withdrawCurrency',
            'parameters': {
                'user_id': user_id,
                'amount': amount
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance_sender'])


    def withdraw_tax_currency(self, user_id: int, amount: int):
        """Withdraw from tax account to users balance using user_id. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'withdrawTaxCurrency',
            'parameters': {
                'user_id': user_id,
                'amount': amount
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance_sender'])


    def spend_currency_taxed(self, user_id: int, amount: int, tax_band: str):
        """Spend users balance using user_id, and tax the transfer. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'spendCurrencyTaxed',
            'parameters': {
                'user_id': user_id,
                'amount': amount,
                'tax_band': ""+tax_band
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance_sender'])


    def withdraw_currency_taxed(self, user_id: int, amount: int, tax_band: str):
        """Withdraw from bank to users balance using user_id, and tax the transfer. Returns users balance afterwards as int. PLEASE READ CODE COMMENT FOR withdrawCurrencyTaxed IN bank/main.py"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'withdrawCurrencyTaxed',
            'parameters': {
                'user_id': user_id,
                'amount': amount,
                'tax_band': ""+tax_band
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance_sender'])


    def summon_currency(self, user_id: int, amount: int):
        """Summon currency and add to users balance using user_id. Returns users balance afterwards as int"""
        # Create payload/request for bank server
        payload = dumps({
            'action': 'summonCurrency',
            'parameters': {
                'user_id_receiver': user_id,
                'amount': amount
            }
        })
        # Create headers
        headers = self.default_headers
        headers['Content-Length'] = str(len(payload))
        headers['Authorization'] = self.config['COMMS_SECRET']
        # Send request
        r = requests.post(url=self.config['COMMS_TARGET']+"/action",
                data=payload,
                headers=headers,
                timeout=10
            )
        content = loads(r.content)
        # If the code is not 200, raise an error with the response of the bank
        if r.status_code != 200:
            self.logger.warn('Bank response was a non 200')
            self.logger.warn(content)
            raise Exception(content)
        if content['request'] != 'Accepted':
            self.logger.warn('Bank response was not Accepted')
            self.logger.warn(content)
        return int(content['response']['balance_receiver'])


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
