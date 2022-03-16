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
from lib.bank_interface import Bank #pylint: disable=E0401
from lib.utils import Utils #pylint: disable=E0401

class Bot:
# NOTE(LIAM):
#       Maybe use nickname and real name for fuzzy matches?


    def __init__(self, logger: Logger, config, bank: Bank, client: discord.Client):
        self.logger = logger
        self.config = config
        self.bank = bank
        self.client = client
        self.guild_id = 0
        # fuzzy percent required to match services
        self.service_fuzzy_percent = 95
        # fuzzy percent required to match users
        self.user_fuzzy_percent = 90
        self.products = {
            'services': [
                {
                    'name': 'Server mute',
                    'description': 'Mute someone on the server for 30 seconds',
                    'price': 2160,
                    'function': self.service_server_mute
                },
                {
                    'name': 'Server deafen',
                    'description': 'Deafen someone on the server for 1 minute',
                    'price': 1440,
                    'function': self.service_server_deafen
                },
                {
                    'name': 'Server disconnect',
                    'description': 'Disconnect someone on the server',
                    'price': 1440,
                    'function': self.service_server_disconnect
                }
            ]
        }


    async def handle_input(self, ctx: commands.context, *args):
        """Handle input for the shop"""
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
        """Handle purchase request"""
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
            if match[1] > self.service_fuzzy_percent:
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
        product_to_call = {}
        for product in self.products['services']:
            if product['name'] == matches[0]:
                product_to_call = product
                func_to_call = product['function']
        try:
            response =  await func_to_call(ctx, product_to_call)
            self.logger.log(f"Service '{product['name']}' is being purchased by {ctx.author.id}")
            self.logger.log(f'Purchase service info: {response}')
        except Exception as e:
            self.logger.error(f"Service '{product['name']}' was purchased by {ctx.author.id} and failed:")
            self.logger.error(str(e))



    async def service_server_mute(self, ctx: commands.context, product):
        """Handle service purchase of server mute"""
        all_active = await self.all_channel_members(self.guild_id)
        if len(all_active) == 0:
            await ctx.reply('No users are online!')
            await ctx.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": 'No users online'
            }
        await ctx.reply('Who is the target? (use the targets server nickname)')

        # Function is parsed into wait_for for validation
        def user_match(message: discord.Message):
            return (message.channel == ctx.channel) and (message.author.id == ctx.author.id)
        message = await self.client.wait_for('message', check=user_match)

        all_active_names = map(lambda member: member.display_name, all_active)
        # Get fuzzy search
        fuzzy = process.extract(message.content, all_active_names)
        matches = []
        for match in fuzzy:
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message.reply('No users match that name')
            await message.add_reaction('❌')
            return
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message.reply('User name was to generic, did you mean?' + ''.join(items))
            await message.add_reaction('❌')
            return
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        # Actually perform action, and spend currency
        user_currency = self.bank.getBalance(ctx.author.id)
        if user_currency < product['price']:
            await message.reply(f'Insufficient balance, current balance is {user_currency} VBC')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": f'Insufficient balance, current balance is {user_currency}'
                }
        await message.add_reaction('✔️')
        self.bank.spendCurrency(ctx.author.id, product['price'])
        await target.edit(mute = True, reason=f'Service purchase: {ctx.author.display_name}')
        async def unmuteFunc(*args):
            member: discord.Member = args[0][0]
            author_name = args[0][1]
            await member.edit(mute = False, reason=f'Service purchase: {author_name}')

        Utils.future_call(30.0, unmuteFunc, [target, ctx.author.display_name])
        # Return info about service purchase
        return {
            "user_id": ctx.author.id,
            "target_name": target.id
            }


    async def service_server_deafen(self, ctx: commands.context, product):
        """Handle service purchase of server deafen"""
        all_active = await self.all_channel_members(self.guild_id)
        if len(all_active) == 0:
            await ctx.reply('No users are online!')
            await ctx.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": 'No users online'
            }
        await ctx.reply('Who is the target? (use the targets server nickname)')

        # Function is parsed into wait_for for validation
        def user_match(message: discord.Message):
            return (message.channel == ctx.channel) and (message.author.id == ctx.author.id)
        message = await self.client.wait_for('message', check=user_match)

        all_active_names = map(lambda member: member.display_name, all_active)
        # Get fuzzy search
        fuzzy = process.extract(message.content, all_active_names)
        matches = []
        for match in fuzzy:
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message.reply('No users match that name')
            await message.add_reaction('❌')
            return
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message.reply('User name was to generic, did you mean?' + ''.join(items))
            await message.add_reaction('❌')
            return
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        # Actually perform action, and spend currency
        user_currency = self.bank.getBalance(ctx.author.id)
        if user_currency < product['price']:
            await message.reply(f'Insufficient balance, current balance is {user_currency} VBC')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": f'Insufficient balance, current balance is {user_currency}'
                }
        await message.add_reaction('✔️')
        self.bank.spendCurrency(ctx.author.id, product['price'])
        await target.edit(deafen = True, reason=f'Service purchase: {ctx.author.display_name}')
        async def unmuteFunc(*args):
            member: discord.Member = args[0][0]
            author_name = args[0][1]
            await member.edit(deafen = False, reason=f'Service purchase: {author_name}')

        Utils.future_call(30.0, unmuteFunc, [target, ctx.author.display_name])
        # Return info about service purchase
        return {
            "user_id": ctx.author.id,
            "target_name": target.id
            }


    async def service_server_disconnect(self, ctx: commands.context, product):
        """Handle service purchase of server disconnect"""
        all_active = await self.all_channel_members(self.guild_id)
        if len(all_active) == 0:
            await ctx.reply('No users are online!')
            await ctx.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": 'No users online'
            }
        await ctx.reply('Who is the target? (use the targets server nickname)')

        # Function is parsed into wait_for for validation
        def user_match(message: discord.Message):
            return (message.channel == ctx.channel) and (message.author.id == ctx.author.id)
        message = await self.client.wait_for('message', check=user_match)

        all_active_names = map(lambda member: member.display_name, all_active)
        # Get fuzzy search
        fuzzy = process.extract(message.content, all_active_names)
        matches = []
        for match in fuzzy:
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message.reply('No users match that name')
            await message.add_reaction('❌')
            return
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message.reply('User name was to generic, did you mean?' + ''.join(items))
            await message.add_reaction('❌')
            return
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        # Actually perform action, and spend currency
        user_currency = self.bank.getBalance(ctx.author.id)
        if user_currency < product['price']:
            await message.reply(f'Insufficient balance, current balance is {user_currency} VBC')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": f'Insufficient balance, current balance is {user_currency}'
                }
        await message.add_reaction('✔️')
        self.bank.spendCurrency(ctx.author.id, product['price'])
        await target.edit(voice_channel=None, reason=f'Service purchase: {ctx.author.display_name}')
        # Return info about service purchase
        return {
            "user_id": ctx.author.id,
            "target_name": target.id
            }


    async def all_channel_members(self, guild_id: int):
        """Returns all members currently in a channel within the guild"""
        online_users = []
        guild: discord.Guild = self.client.get_guild(guild_id)
        for channel in guild.voice_channels:
            for member in channel.members:
                online_users.append(member)
        return online_users


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
