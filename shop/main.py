# Shop Bot
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
from lib.shared import Shared #pylint: disable=E0401
from lib.coin_manager import CoinManager #pylint: disable=E0401
from lib.utils import Utils #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'shop'
config = configparser.ConfigParser()
config.read('./config/config.ini') # CHANGE ME
config = config[bot_type]
config.bot_type = bot_type
config.version = 'v1.0'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (1643898208064)
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
bot = Bot(logger, config, bank, client, cm)


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


@client.command(name='shop')
async def command_shop(ctx: commands.Context, *args):
    """Access the store"""
    await bot.handle_input(ctx, *args)


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
