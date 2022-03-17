# Chameleon Bot
# Handles TTS messages
####################################################################################################
import discord
import os, sys, json
import configparser
import discord
from discord.ext import commands

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.bank_interface import Bank #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'chameleon'
config = configparser.ConfigParser()
config.read('./config.ini') # CHANGE ME
config = config[bot_type]

VERSION = 'v1.0'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (534790879296)
intents = discord.Intents.default()
intents.members = True
intents.dm_messages = True
intents.messages = True

logger = Logger(int(config['LOGGING_LEVEL']), config['WRITE_TO_LOG_FILE'], config['LOG_FILE_DIR'])
if ('LOGGING_PREFIX' in config and 'LOGGING_PREFIX_SIZE' in config):
    logger.custom_prefix = config['LOGGING_PREFIX']
    logger.custom_prefix_size = int(config['LOGGING_PREFIX_SIZE'])
logger.log(f'Starting {bot_type} - ' + VERSION)

client = commands.Bot(command_prefix=config['COMMAND_PREFIX'], intents=intents)
bot = Bot(logger, config, client)
bank = Bank(logger, config)


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


@client.command(name='tts')
async def command_tts(ctx: commands.Context, *args):
    """Execute tts command""" 

    user_balance = bank.getBalance(ctx.author.id)
    # insufficient balance
    if int(config['TTS_COST']) >= user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} VBC')
        return
    # Perform tts and spend currency
    try:
        await bot.send_tts(ctx, args)
        bank.spendCurrency(ctx.author.id, int(config['TTS_COST']))

    except Exception as e:
        logger.warn('Failed to execute tts:')
        logger.warn(str(e))


@client.command(name='version')
async def command_version(ctx: commands.Context, *args):
    """View bot version"""
    if len(args) == 0 or args[0] == bot_type:
        await ctx.message.reply(VERSION)


@client.command(name=' ', aliases=config['IGNORE_COMMANDS'].split(','))
async def command_nothing(ctx: commands.Context, *args):
    """"""# Catch to do nothing. Used for overlapping bot prefix

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
