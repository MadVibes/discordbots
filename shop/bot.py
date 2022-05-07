# This handles the actual bot logic
####################################################################################################
from discord.ext import commands
from discord import VoiceChannel
from fuzzywuzzy import process
import sys, math, random, time
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.bank_interface import Bank #pylint: disable=E0401
from lib.utils import Utils #pylint: disable=E0401
from lib.coin_manager import CoinManager #pylint: disable=E0401

class Bot:
# NOTE(LIAM):
#       Maybe use nickname and real name for fuzzy matches?

    def __init__(self, logger: Logger, config, bank: Bank, client: discord.Client, coin_manager: CoinManager):
        self.logger = logger
        self.config = config
        self.bank = bank
        self.client = client
        self.guild_id = 0
        self.cm = coin_manager
        # fuzzy percent required to match services
        self.service_fuzzy_percent = 95
        # fuzzy percent required to match users
        self.user_fuzzy_percent = 90
        self.timeouts = {}
        self.products = {
            'services': [
                {
                    'name': 'Mute',
                    'description': 'Mute someone on the server for 30 seconds',
                    'price': 600,
                    'function': self.service_server_mute
                },
                {
                    'name': 'Deafen',
                    'description': 'Deafen someone on the server for 1 minute',
                    'price': 660,
                    'function': self.service_server_deafen
                },
                {
                    'name': 'Disconnect',
                    'description': 'Disconnect someone on the server',
                    'price': 420,
                    'function': self.service_server_disconnect
                },
                {
                    'name': 'Change nickname',
                    'description': 'Change target nickname',
                    'price': 800,
                    'function': self.service_rename
                },
                {
                    'name': 'Exile',
                    'description': 'Push someone into the AFK channel, Has cooldown',
                    'price': 90,
                    'function': self.service_afk_move,
                    'timeout': 600
                }
            ]
        }


    async def handle_input(self, ctx: commands.context, *args):
        """Handle input for the shop"""
        # If no args are given
        if len(args) == 0:
            await ctx.reply('Invalid arguments, see help menu `$shop help`')
        # arg = help
        elif args[0] == 'help':
            await ctx.reply('Hehe, yeah i\'ll implement this at somepoint :) Just do `$shop list`')
        # arg = list
        elif args[0] == 'list':
            embed = discord.Embed(name='Shopping list',
                    description='Available items in the shop\n DO NOT DM THE BOT TO PERFORM ACTIONS! (KNOWN BUG)',
                    inline=True)
            for service in self.products['services']:
                embed.add_field(name=service['name'],
                        value=str(service['price']) +  f' {self.cm.currency()}\n'  + service['description'],
                        inline=True)
            # Add random json
            product_json = self.generate_random_json()
            embed.add_field(name=product_json['name'],
                        value=str(product_json['price']) +  f' {self.cm.currency()}\n'  + product_json['description'],
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
        service_names.append(self.generate_random_json()['name'])
        # Get fuzzy search
        fuzzy = process.extract(query, service_names)
        self.logger.debug('Fuzzy matches in purchase action:')
        matches = []
        for match in fuzzy:
            self.logger.debug(f'{match[0]}:{match[1]}')
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
            await ctx.reply('Shop purchase request was too generic, did you mean?' + ''.join(items))
            return
        # Actually execute function attached to shop service/product
        product_to_call = {}; func_to_call = None
        if self.generate_random_json()['name'] == matches[0]:
            product_to_call = self.generate_random_json()
            func_to_call = product_to_call['function']
        else:
            for product in self.products['services']:
                if product['name'] == matches[0]:
                    product_to_call = product
                    func_to_call = product['function']
        try:
            response = await func_to_call(ctx, product_to_call)
            # If response contains an error, raise exception
            if 'error' in response:
                raise Exception(response['error'])
            elif 'warning' in response:
                self.logger.log(f"Service '{product_to_call['name']}' is being purchased by {ctx.author.id}")
                self.logger.log(f'Attempted purchase service info: {response}')
            else:
                self.logger.log(f"Service '{product_to_call['name']}' was purchased by {ctx.author.id} and cancelled:")
                self.logger.log(f'Purchased service info: {response}')
        except Exception as e:
            self.logger.error(f"Service '{product_to_call['name']}' was purchased by {ctx.author.id} and failed:")
            self.logger.error(str(e))


    async def service_server_mute(self, ctx: commands.context, product):
        """Handle service purchase of server mute"""
        all_active = await self.all_channel_members(self.guild_id)
        if len(all_active) == 0:
            await ctx.reply('No users are online!')
            await ctx.message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": 'No users online'
            }
        await ctx.reply('Who is the target? (use the targets server nickname)')

        # Function is parsed into wait_for for validation
        def user_match(message: discord.Message):
            return (message.channel == ctx.channel) and (message.author.id == ctx.author.id)
        message = await self.client.wait_for('message', check=user_match)

        all_active_names = map(lambda member: member.display_name, all_active)
        # Get fuzzy search
        fuzzy = process.extract(message.content, all_active_names)
        self.logger.debug('Fuzzy matches in service server mute action:')
        matches = []
        for match in fuzzy:
            self.logger.debug(f'{match[0]}:{match[1]}')
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message.reply('No users match that name')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'No users matches that name'
                }
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message.reply('User name was too generic, did you mean?' + ''.join(items))
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Too many users matches that name'
                }
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        # Actually perform action, and spend currency
        user_currency = self.bank.get_balance(ctx.author.id)
        if user_currency < product['price']:
            await message.reply(f'Insufficient balance, current balance is {user_currency} {self.cm.currency()}')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Insufficient balance, current balance is {user_currency}'
                }
        self.bank.spend_currency_taxed(ctx.author.id, product['price'], self.config['SERVICE_TAX_BAND'])
        await target.edit(mute = True, reason=f'Service purchase: Anonymous')
        await message.add_reaction('✅')
        async def unmuteFunc(*args):
            member: discord.Member = args[0][0]
            await member.edit(mute = False, reason=f'Service purchase: Anonymous')

        Utils.future_call(30.0, unmuteFunc, [target])
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
            await ctx.message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": 'No users online'
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
            self.logger.debug(f'{match[0]}:{match[1]}')
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message.reply('No users match that name')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'No users matches that name'
                }
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message.reply('User name was too generic, did you mean?' + ''.join(items))
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Too many users matches that name'
                }
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        # Actually perform action, and spend currency
        user_currency = self.bank.get_balance(ctx.author.id)
        if user_currency < product['price']:
            await message.reply(f'Insufficient balance, current balance is {user_currency} {self.cm.currency()}')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Insufficient balance, current balance is {user_currency}'
                }
        self.bank.spend_currency_taxed(ctx.author.id, product['price'], self.config['SERVICE_TAX_BAND'])
        await target.edit(deafen = True, reason=f'Service purchase: Anonymous')
        await message.add_reaction('✅')
        async def unmuteFunc(*args):
            member: discord.Member = args[0][0]
            await member.edit(deafen = False, reason=f'Service purchase: Anonymous')

        Utils.future_call(30.0, unmuteFunc, [target])
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
            await ctx.message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": 'No users online'
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
            self.logger.debug(f'{match[0]}:{match[1]}')
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message.reply('No users match that name')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'No users matches that name'
                }
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message.reply('User name was too generic, did you mean?' + ''.join(items))
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Too many users matches that name'
                }
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        # Actually perform action, and spend currency
        user_currency = self.bank.get_balance(ctx.author.id)
        if user_currency < product['price']:
            await message.reply(f'Insufficient balance, current balance is {user_currency} {self.cm.currency()}')
            await message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Insufficient balance, current balance is {user_currency}'
                }
        self.bank.spend_currency_taxed(ctx.author.id, product['price'], self.config['SERVICE_TAX_BAND'])
        await target.edit(voice_channel=None, reason=f'Service purchase: Anonymous')
        await message.add_reaction('✅')
        # Return info about service purchase
        return {
            "user_id": ctx.author.id,
            "target_name": target.id
            }


    async def service_rename(self, ctx: commands.context, product):
        """Handle service purchase of server timeout"""
        all_active = await self.all_server_members(self.guild_id)
        if len(all_active) == 0:
            await ctx.reply('No users are online!')
            await ctx.message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": 'No users online'
            }
        await ctx.reply('Who is the target? (use the targets server nickname)')

        # Function is parsed into wait_for for validation
        def user_match(message: discord.Message):
            return (message.channel == ctx.channel) and (message.author.id == ctx.author.id)
        message_user = await self.client.wait_for('message', check=user_match)

        all_active_names = map(lambda member: member.display_name, all_active)
        # Get fuzzy search
        fuzzy = process.extract(message_user.content, all_active_names)
        matches = []
        for match in fuzzy:
            self.logger.debug(f'{match[0]}:{match[1]}')
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message_user.reply('No users match that name')
            await message_user.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'No users matches that name'
                }
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message_user.reply('User name was too generic, did you mean?' + ''.join(items))
            await message_user.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Too many users matches that name'
                }
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        await message_user.reply('What shall their new name be?')
        message_name = await self.client.wait_for('message', check=user_match)

        # Actually perform action, and spend currency
        user_currency = self.bank.get_balance(ctx.author.id)
        if user_currency < product['price']:
            await message_name.reply(f'Insufficient balance, current balance is {user_currency} {self.cm.currency()}')
            await message_name.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Insufficient balance, current balance is {user_currency}'
                }
        self.bank.spend_currency_taxed(ctx.author.id, product['price'], self.config['SERVICE_TAX_BAND'])
        await target.edit(nick=message_name.content, reason=f'Service purchase: Anonymous')
        await message_name.add_reaction('✅')
        # Return info about service purchase
        return {
            "user_id": ctx.author.id,
            "target_name": target.id
            }


    async def service_afk_move(self, ctx: commands.context, product):
        """Handle service purchase of moving user to AFK channel"""
        timeout_id = 'service_afk_move'
        if self.timeout_active(product, timeout_id):
            time_left = int(product['timeout'] - (time.time()-self.timeouts['service_afk_move']))
            await ctx.reply(f'Timeout is active! {time_left} seconds remaining...')
            return {
                "user_id": ctx.author.id,
                "warning": f'Timeout is active, time left: {time_left}'
            }
        all_active = await self.all_server_members(self.guild_id)
        if len(all_active) == 0:
            await ctx.reply('No users are online!')
            await ctx.message.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": 'No users online'
            }
        await ctx.reply('Who is the target? (use the targets server nickname)')

        # Function is parsed into wait_for for validation
        def user_match(message: discord.Message):
            return (message.channel == ctx.channel) and (message.author.id == ctx.author.id)
        message_user = await self.client.wait_for('message', check=user_match)

        all_active_names = map(lambda member: member.display_name, all_active)
        # Get fuzzy search
        fuzzy = process.extract(message_user.content, all_active_names)
        matches = []
        for match in fuzzy:
            self.logger.debug(f'{match[0]}:{match[1]}')
            if match[1] == 100:
                matches = [match]
                break
            if match[1] > self.user_fuzzy_percent:
                matches.append(match[0])
        if len(matches) == 0:
            await message_user.reply('No users match that name')
            await message_user.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'No users matches that name'
                }
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await message_user.reply('User name was too generic, did you mean?' + ''.join(items))
            await message_user.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Too many users matches that name'
                }
        target: discord.Member = None
        for active in all_active:
            if active.display_name == matches[0][0]:
                target = active

        afk_channel: VoiceChannel = ctx.guild.afk_channel
        if afk_channel is None:
            await message_user.reply(f'No AFK channel is assigned in this discord!')
            await message_user.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "error": f'No assigned AFK channel'
                }

        # Actually perform action, and spend currency
        user_currency = self.bank.get_balance(ctx.author.id)
        if user_currency < product['price']:
            await message_user.reply(f'Insufficient balance, current balance is {user_currency} {self.cm.currency()}')
            await message_user.add_reaction('❌')
            return {
                "user_id": ctx.author.id,
                "warning": f'Insufficient balance, current balance is {user_currency}'
                }
        self.bank.spend_currency_taxed(ctx.author.id, product['price'], self.config['SERVICE_TAX_BAND'])
        await target.move_to(afk_channel, reason=f'Service purchase: Anonymous')
        await message_user.add_reaction('✅')
        self.timeout_init(timeout_id)
        # Return info about service purchase
        return {
            "user_id": ctx.author.id,
            "target_name": target.id
            }


    async def random_service(self, ctx: commands.context, product):
        """Run a random service using self.products"""
        services = self.products['services']
        random_service_index = random.randint(0, len(services)-1)
        product_to_call = services[random_service_index]
        function_to_call = product_to_call['function']
        # Actually call function and return whatever it produces
        # Parse in the random product, this means it'll use the correct price
        return await function_to_call(ctx, product)


    async def all_channel_members(self, guild_id: int):
        """Returns all members currently in a channel within the guild"""
        online_users = []
        guild: discord.Guild = self.client.get_guild(guild_id)
        for channel in guild.voice_channels:
            for member in channel.members:
                online_users.append(member)
        return online_users


    async def all_server_members(self, guild_id: int):
        """Returns all members on a discord server within a guild"""
        users = []
        generator = self.client.get_all_members()
        for user in generator:
            users.append(user)
        return users


    def generate_random_json(self):
        """Generate JSON for random option"""
        count = 0; total = 0
        for service in self.products['services']:
            count += 1
            total += service['price']

        return {
            'name': 'Random',
            'description': 'Perform a completely random action',
            'price': math.floor(total/count),
            'function': self.random_service
        }


    def timeout_active(self, product, id):
        """Checks if a timeout has expired on id"""
        if self.timeouts == {}:
            return False
        # No active timeout for id
        elif id not in self.timeouts:
            return False
        # Timeout has now expired
        elif (time.time()-self.timeouts[id]) >= product['timeout']:
            self.timeouts.pop(id)
            return False
        # Timeout must be active
        else:
            return True


    def timeout_init(self, id):
        """Start a timeout on a id"""
        self.timeouts[id] = time.time()


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
