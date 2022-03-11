# This handles the actual bot logic
####################################################################################################
from datetime import datetime
from discord.ext import commands
from discord import Color
from fuzzywuzzy import process
import sys
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401

class Bot:


    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client
        # fuzzy percent required to match
        self.fuzzy_percent = 95
        self.products = {
            'services': [
                {
                    'name': 'Server mute',
                    'description': 'Mute someone on the server for 30 seconds',
                    'price': 2160,
                    'params': ['target'],
                    'function': self.testFunc
                },
                {
                    'name': 'Server deafen',
                    'description': 'Deafen someone on the server for 1 minutes',
                    'price': 1440,
                    'params': ['target']
                },
                {
                    'name': '1111',
                    'description': 'Deafen someone on the server for 1 minutes',
                    'price': 1111,
                    'params': ['target']
                },
                {
                    'name': '2222',
                    'description': 'Deafen someone on the server for 1 minutes',
                    'price': 2222,
                    'params': ['target']
                },
                {
                    'name': '3333',
                    'description': 'Deafen someone on the server for 1 minutes',
                    'price': 3333,
                    'params': ['target']
                },
                {
                    'name': '4444',
                    'description': 'Deafen someone on the server for 1 minutes',
                    'price': 4444,
                    'params': ['target']
                }
            ]
        }


    async def handle_input(self, ctx: commands.context, *args):
        """Handle the purchase of a service"""
        # If no args are given
        if len(args) == 0:
            ctx.reply('Invalid arguments, see help menu `!shop help`')
        # arg = help
        elif args[0] == 'help':
            ctx.reply('Hehe, yeah i\'ll implement this at somepoint :)')
        # arg = list
        elif args[0] == 'list':
            embed = discord.Embed(name='Shopping list',
                    description='Available items in the shop',
                    inline=True)
            for service in self.products['services']:
                embed.add_field(name=service['name'],
                        value=str(service['price']) +  ' VBC\n'  + service['description'],
                        inline=True)
            await ctx.send(embed=embed)
        # args = buy, and query string provided
        elif args[0] == 'buy' and len(args[1]) > 0:
            await self.handle_purchase(ctx, args)


    async def handle_purchase(self, ctx: commands.context, args):
        if len(args) > 2:
            query = ' '.join(args[1:len(args)]) # Get query string by combining anything after 'buy' (index 1)
        else:
            query = args[1] # Else, get only arguement after 'buy'
        service_names = []
        for service in self.products['services']:
            service_names.append(service['name'])
        # Get fuzzy search
        fuzzy = process.extract(query, service_names)
        matches = []
        for match in fuzzy:
            if match[1] > self.fuzzy_percent:
                matches.append(match[0])
        # Handle matches
        # 0 matches
        if len(matches) == 0:
            await ctx.reply('No shop items match that name')
            return
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await ctx.reply('Shop purchase request was to generic, did you mean?' + ''.join(items))
            return
        # Actually execute function attached to shop service/product
        print(matches[0])
        for product in self.products['services']:
            if product['name'] == matches[0]:
                func_to_call = product['function']
        await func_to_call()

    async def testFunc(self):
        print('TempCall')


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
