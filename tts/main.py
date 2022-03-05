# Bank Bot
# Handles the moving/maintaining of VibeCoin
####################################################################################################
from dis import discord
import os, sys
from re import A
import configparser
import discord
from discord.ext import tasks
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
            bot.guild_id = guild.id
            break
        else:
            logger.error('Failed to find guild from config! shutting down :(')
            exit(1)

    # Start loops
    balance_accrue.start()
    

@client.event
async def on_message(message: discord.Message):
    # If the user does not exist, add them to DB
    if not(bot.user_id_exists(int(message.author.id))):
        success = bot.create_user(int(message.author.id), message.author.display_name)
        if not(success):
            logger.warn(f'Failed to create new user {message.author.display_name}')

@tasks.loop(minutes=float(config['BALANCE_LOOP']))
async def balance_accrue():
    """Accrue balance to users currently in a channel"""
    online_users = []

    guild: discord.Guild = client.get_guild(bot.guild_id)
    for channel in guild.voice_channels:
        if channel.name != guild.afk_channel.name:
            for member in channel.members:
                online_users.append(member)

    for online_user in online_users:
        if not(bot.user_id_exists(int(online_user.id))):
            bot.create_user(int(online_user.id), online_user.display_name)
        bot.alter_balance(int(config['BALANCE_ACCRUE']), online_user.id)


# Start the bot using TOKEN
client.run(TOKEN)