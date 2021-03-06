# Sample user
# Sits in channel from config file
# Relays DMs to chat
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

# CONFIGS/LIBS
########################################################################################################
bot_type = sys.argv[1]
config = configparser.ConfigParser()
config.read('./config/config.ini') # CHANGE ME
config = config[bot_type]

VERSION = 'v1.0'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (1644972474359)
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
bank = Bank(logger, config)
guild_id = 0


@client.event
async def on_ready():
    logger.log(f'Connected to Discord! uid:{client.user.id}')
    guild_temp = None
    for guild in client.guilds:
        if guild.name == GUILD:
            guild_id = guild.id
            guild_temp = guild
            break
        else:
            logger.error('Failed to find guild from config! shutting down :(')
            exit(1)
    for channel in guild_temp.channels:
        if channel.name == config['JOIN_CHANNEL']:
            await channel.connect()


@client.event
async def on_message(message: discord.Message):
    """DM Relay - forwards DMs to guild chat"""
    try:
        if message.author.id != client.user.id and message.channel.type is discord.ChannelType.private:
            # Handle normal on_message event
            for guild in client.guilds:
                for channel in guild.text_channels:
                    await channel.send(message.content)
    except Exception as e:
        logger.error(f'{bot_type} failed')
        logger.error(str(e))


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
