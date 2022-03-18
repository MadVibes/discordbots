# Bank Bot
# Handles the moving/maintaining of VibeCoin
####################################################################################################
import discord
import os, sys, json
import configparser
import discord
from discord.ext import tasks
from discord.ext import commands

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.server import Web_Server #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'bank'
config = configparser.ConfigParser()
config.read('./config.ini') # CHANGE ME
config = config[bot_type]

VERSION = 'v1.0'

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
logger.log(f'Starting {bot_type} - ' + VERSION)

client = commands.Bot(command_prefix=config['COMMAND_PREFIX'], intents=intents)
bot = Bot(logger, config, client)

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

    # Start loops
    balance_accrue.start()
    balance_fade.start()
    # Create it's own user in bank
    if not bot.user_id_exists(client.user.id):
        bot.create_user(client.user.id, client.user.name)
    # Restore defaults
    await client.get_guild(bot.guild_id).get_member(client.user.id).edit(nick=config['DEFAULT_NAME'])
    if config['STATUS_START_ONLINE'] == 'True':
        await client.change_presence(status=discord.Status.online)
    else:
        await client.change_presence(status=discord.Status.invisible)


@client.event
async def on_message(message: discord.Message):
    # If the user does not exist, add them to DB
    if not(bot.user_id_exists(int(message.author.id))):
        success = bot.create_user(int(message.author.id), message.author.display_name)
        if not(success):
            logger.warn(f'Failed to create new user {message.author.display_name}')

    # Handle normal on_message event
    await client.process_commands(message)


@tasks.loop(minutes=float(config['BALANCE_ACCRUE_TIME']))
async def balance_accrue():
    """Accrue balance to users currently in a channel"""
    online_users = []

    guild: discord.Guild = client.get_guild(bot.guild_id)
    for channel in guild.voice_channels:
        # Skip afk channel
        if channel.name != guild.afk_channel.name:
            for member in channel.members:
                # Skip giving coin on conditions
                #   1. deafened
                #   2. only 1 person in channel
                if not(member.voice.self_deaf
                    and len(channel.members)==1):
                    online_users.append(member)

    for online_user in online_users:
        if not(bot.user_id_exists(int(online_user.id))):
            bot.create_user(int(online_user.id), online_user.display_name)
        bot.alter_balance(int(config['BALANCE_ACCRUE']), online_user.id)


@tasks.loop(minutes=float(config['BALANCE_FADE_TIME']))
async def balance_fade():
    """Fade balance to users currently in a channel and afk"""
    afk_users = []

    guild: discord.Guild = client.get_guild(bot.guild_id)

    # Afk channel
    for channel in guild.voice_channels:
        for member in channel.members:
            afk_users.append(member)

    for channel in guild.voice_channels:
        # Skip afk channel
        if channel.name != guild.afk_channel.name:
            for member in channel.members:
                # fade coin on conditions
                #   1. deafened
                if member.voice.self_deaf:
                    afk_users.append(member)

    for afk_user in afk_users:
        if not(bot.user_id_exists(int(afk_user.id))):
            bot.create_user(int(afk_user.id), afk_user.display_name)
        bot.alter_balance(-int(config['BALANCE_FADE']), afk_user.id)


@client.command(name='balance')
async def command_balance(ctx: commands.Context, *args):
    """Display a users balance"""
    if not(bot.user_id_exists(int(ctx.author.id))):
        bot.create_user(int(ctx.author.id), ctx.author.display_name)

    balance = bot.get_balance(ctx.author.id)
    await ctx.send(f'Your current balance is {balance} VBC')


@client.command(name='transfer')
async def command_transfer(ctx: commands.Context, *args):
    """Tansfer money to another player"""


@client.command(name='version')
async def command_tts(ctx: commands.Context, *args):
    """View bot version""" 
    if len(args) == 0 or args[0] == bot_type:
        await ctx.message.reply(VERSION)


@client.command(name=' ', aliases=config['IGNORE_COMMANDS'].split(','))
async def command_nothing(ctx: commands.Context, *args):
    """"""# Catch to do nothing. Used for overlapping bot prefix


# WEB SERVER INIT
########################################################################################################

# Mini service/class for actions
class Servlet:
    def __init__(self, client: discord.Client, bot: Bot):
        self.client = client
        self.bot = bot


# Functions for webserver
def getBalance(service: Servlet, parameters: json):
    """Return users balance"""
    if 'user_id' not in parameters:
        raise Exception('user_id was not included in parameters')

    return service.bot.req_get_balance(user_id=parameters['user_id'])


def moveCurrency(service: Servlet, parameters: json):
    """Move balance from one user to another"""
    if ('user_id_sender' not in parameters
        or 'user_id_receiver' not in parameters
        or 'amount' not in parameters):
        raise Exception('user_id_sender, user_id_receiver, amount were not all included in parameters')

    return service.bot.req_move_currency(user_id_sender=parameters['user_id_sender'], user_id_receiver=parameters['user_id_receiver'], amount=parameters['amount'])


def spendCurrency(service: Servlet, parameters: json):
    """Spend balance of user"""
    if ('user_id' not in parameters
        or 'amount' not in parameters):
        raise Exception('user_id, amount were not all included in parameters')

    return service.bot.req_move_currency(user_id_sender=parameters['user_id'], user_id_receiver=service.client.user.id, amount=parameters['amount'])


def withdrawCurrency(service: Servlet, parameters: json):
    """Withdraw balance of bank"""
    if ('user_id' not in parameters
        or 'amount' not in parameters):
        raise Exception('user_id, amount were not all included in parameters')

    return service.bot.req_move_currency(user_id_sender=service.client.user.id, user_id_receiver=parameters['user_id'], amount=parameters['amount'])


# Mapping of possible functions that the web server can call
actions = {
    'getBalance': getBalance,
    'moveCurrency': moveCurrency,
    'spendCurrency': spendCurrency,
    'withdrawCurrency': withdrawCurrency
}
servlet = Servlet(client, bot)

web = Web_Server(logger, actions, servlet, config)
web.start()

# Start the bot using TOKEN
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
