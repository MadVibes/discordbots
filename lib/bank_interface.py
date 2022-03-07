# Bank interface
# Handles interfacing with the bank bot udner the hood to make lazy devs time easier sending HTTP requests
###########################################################################################################
import requests, sys
from json import dumps, loads

sys.path.insert(0, '../')
from lib.logger import Logger

class Bank:

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config
        self.default_headers = {
            'Content-Type': 'application/json'
        }

    def getBalance(self, user_id: int):
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

    def spendCurrency(self, user_id: int, amount: int):
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