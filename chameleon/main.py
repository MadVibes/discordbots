# Bank Bot
# Handles the moving/maintaining of VibeCoin
####################################################################################################
import discord
import os, sys, json
import configparser
import discord
from discord.ext import tasks
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

intents = discord.Intents.default()
intents.members = True
intents.dm_messages = True

logger = Logger(int(config['LOGGING_LEVEL']), bool(config['WRITE_TO_LOG_FILE']), config['LOG_FILE_DIR'])
logger.log('Starting Chameleon - ' + VERSION)
client = discord.Client(intents=intents)
bot = Bot(logger, config, client)

@client.event
async def on_ready():
    logger.log(f'Connected to Discord! {client.user.id}')
    for guild in client.guilds:
        if guild.name == GUILD:
            bot.guild_id = guild.id
            break
        else:
            logger.error('Failed to find guild from config! shutting down :(')
            exit(1)
    

@client.event
async def on_message(message: discord.Message):
    """Do nothing"""

# Start the bot using TOKEN
client.run(TOKEN)