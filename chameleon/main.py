# Chameleon Bot
# Handles TTS messages
####################################################################################################
import discord
import os, sys, json
import configparser
import discord
from discord.ext import commands
from dotenv import load_dotenv

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
config = configparser.ConfigParser()
config.read('/home/liam/Documents/vibebots/config.ini') # CHANGE ME
config = config['chameleon']

VERSION = 'v0.1'

load_dotenv()
TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (534790879296)
intents = discord.Intents.default()
intents.members = True
intents.dm_messages = True
intents.messages = True

logger = Logger(int(config['LOGGING_LEVEL']), bool(config['WRITE_TO_LOG_FILE']), config['LOG_FILE_DIR'])
logger.log('Starting Chameleon - ' + VERSION)
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

    # Restore defaults
    await client.get_guild(bot.guild_id).get_member(client.user.id).edit(nick=config['TTS_DEFAULT_NAME'])

@client.command(name='tts')
async def command_tts(ctx: commands.Context, *args):

    await bot.can_afford()

    print('SEND TTS!')
    # await bot.send_tts(ctx, args)

# Start the bot using TOKEN
client.run(TOKEN)