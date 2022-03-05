# Bank Bot
# Handles the moving/maintaining of VibeCoin
####################################################################################################
import os, sys
import configparser
import discord
from dotenv import load_dotenv

sys.path.insert(0, '../')
from lib.logger import Logger
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
config = configparser.ConfigParser()
config.read('./config.ini')
config = config['bank']

VERSION = 'v0.1'

load_dotenv()
TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
# GET BOT:
# URL: https://discord.com/api/oauth2/authorize?client_id=949437220450861066&permissions=534791059520&scope=bot
########################################################################################################

intents = discord.Intents.default()
intents.members = True

logger = Logger(int(config['LOGGING_LEVEL']), bool(config['WRITE_TO_LOG_FILE']), config['LOG_FILE_DIR'])
logger.log('Starting Bank - ' + VERSION)
client = discord.Client(intents=intents)
bot = Bot(logger, config, client)

@client.event
async def on_ready():
    logger.log('Connected to Discord!')
    for guild in client.guilds:
        if guild.name == GUILD:
            break
        else:
            logger.error('Failed to find guild from config! shutting down :(')
            exit(1)

@client.event
async def on_message(message: discord.Message):
    # If the user does not exist, add them to DB
    if not(bot.user_id_exists(int(message.author.id))):
        success = bot.create_user(int(message.author.id), message.author.display_name)
        if not(success):
            logger.warn(f'Failed to create new user {message.author.display_name}')

    


# Start the bot using TOKEN
client.run(TOKEN)

