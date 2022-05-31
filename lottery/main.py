# Lottery Bot
# Handles the weekly draw of the Vibebots lottery
####################################################################################################
import discord
import os, sys, json, math, configparser
from fuzzywuzzy import process
from discord.ext import tasks
from discord.ext import commands
from datetime import datetime
import asyncio

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.bank_interface import Bank #pylint: disable=E0401
from lib.server import Web_Server #pylint: disable=E0401
from lib.shared import Shared #pylint: disable=E0401
from lib.emote_manager import CoinManager, ScratchManager
from lib.utils import Utils #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'lottery'
config = configparser.ConfigParser()
config.read('./config/config.ini') # CHANGE ME
config = config[bot_type]
config.bot_type = bot_type
config.version = 'v1.0'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (534790879296)
intents = discord.Intents.default()
intents.members = True #pylint: disable=E0237
intents.dm_messages = True #pylint: disable=E0237
intents.messages = True #pylint: disable=E0237

logger = Logger(int(config['LOGGING_LEVEL']), config['WRITE_TO_LOG_FILE'], config['LOG_FILE_DIR'])
if ('LOGGING_PREFIX' in config and 'LOGGING_PREFIX_SIZE' in config):
    logger.custom_prefix = config['LOGGING_PREFIX']
    logger.custom_prefix_size = int(config['LOGGING_PREFIX_SIZE'])
logger.log(f'Starting {bot_type} - ' + config.version)


client = commands.Bot(command_prefix=config['COMMAND_PREFIX'], intents=intents)
bank = Bank(logger, config)
cm = CoinManager(logger)
sm = ScratchManager(logger)
bot = Bot(logger, config, bank, client, cm, sm)


@tasks.loop(seconds=59)
async def lotto_date_check():
    if datetime.today().weekday() == 4 and datetime.today().hour == 17:

        if datetime.today().minute == 0:
            balance_check = bot.check_tax_balance()
            if balance_check == True:
                await bot.announcement() # Game announcement
    
        elif datetime.today().minute == 10:
            await bot.toggle_purchases() # Turning purchases on

        elif datetime.today().minute == 20:
            await bot.lottery_game() # The game beginning / turning purchases off


@client.event
async def on_ready():
    logger.log(f'Connected to Discord! uid:{client.user.id}')
    for guild in client.guilds:
        if guild.name == GUILD:
            bot.guild_id = guild.id
            break
        else:
            logger.error('Failed to find guild from config! shutting down :(')
            exit(1)

    # Restore defaults
    await client.get_guild(bot.guild_id).get_member(client.user.id).edit(nick=config['DEFAULT_NAME'])
    if config['STATUS_START_ONLINE'] == 'True':
        await client.change_presence(status=discord.Status.online)
    else:
        await client.change_presence(status=discord.Status.invisible)
    # Load cogs
    client.add_cog(Shared(client, config))
    # Load CoinManager
    cm.set_guild(client.get_guild(bot.guild_id))
    async def initCM(*args):
        cm: CoinManager = args[0][0]
        await cm.populate_bot_emojis()
    time = 30 # Seconds
    Utils.future_call(time, initCM, [cm])
    # Load ScratchManager
    sm.set_guild(client.get_guild(bot.guild_id))
    await sm.try_add_emojis(config['EMOJI_SOURCE'])

    lotto_date_check.start()


@client.command(name='lotto')
@commands.guild_only()
async def lotto(ctx, arg, arg2=None):
    """
    Purchase and use a lottery ticket.
    Usage:
        lotto buy [NUMBER]
        lotto random [AMOUNT]
        lotto taken
        lotto set
        lotto help
    """

    if arg.lower() == "buy" and arg2 != None and arg2.isdigit(): # Used to buy lottery tickets
        if int(arg2) in range(1, 101):
            await bot.buy_ticket(ctx, int(arg2))
    
    elif arg.lower() == "taken": # Invoke the embed for showing what numbers are still available
        await bot.number_check(ctx)

    elif arg.lower() == "random" and arg2.isdigit(): # Buying a specified amount of random tickets
        if int(arg2) < 101:
            await bot.buy_random(ctx, int(arg2))
        else:
            await ctx.send("There are only 100 numbers to buy... Don't be a chump and buy them all, party pooper.")

    elif arg.lower() == "set": # Setting the lottery announcement channel
        channel_options = await bot.posting_channel_choices(ctx)
        user_choice = await client.wait_for('message', check=lambda m: m.author.id == ctx.author.id, timeout=15.0)
        try:
            if user_choice.content.isdigit():
                if int(user_choice.content) in channel_options:
                    await bot.set_posting_channel(ctx, int(channel_options[int(user_choice.content)]))
                else:
                    await ctx.send("Wait a minute, that number isn't on the list, please try again.")
            else:
                await ctx.send("Oops! You need to use the numbers, not the names.")

        except asyncio.TimeoutError:
          await ctx.send("Command timed out.")

    elif arg.lower() == "inv":
        await bot.check_player_tickets(ctx)

# Start the bot using TOKENS
client.run(TOKEN)

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
