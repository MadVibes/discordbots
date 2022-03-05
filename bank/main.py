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
config = config['bank']

VERSION = 'v0.1'

load_dotenv()
TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

intents = discord.Intents.default()
intents.members = True
intents.dm_messages = True

logger = Logger(int(config['LOGGING_LEVEL']), bool(config['WRITE_TO_LOG_FILE']), config['LOG_FILE_DIR'])
logger.log('Starting Bank - ' + VERSION)
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

    # Start loops
    balance_accrue.start()
    

@client.event
async def on_message(message: discord.Message):
    # If the user does not exist, add them to DB
    if not(bot.user_id_exists(int(message.author.id))):
        success = bot.create_user(int(message.author.id), message.author.display_name)
        if not(success):
            logger.warn(f'Failed to create new user {message.author.display_name}')
    
    # Is a direct message (This is a null check)
    if not message.guild:
        await on_message_dm(message)
        return

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

async def on_message_dm(message: discord.Message):
    """Handle direct messages from other bots"""
    content = str(message.content).split(config['COMMS_DELIM'])
    if(len(content) != 2):
        logger.warn('Invalid request DM:' + str(message.content))
        return 

    if content[0] not in config['COMMS_ACCEPTED_SECRET']:
        logger.warn('Invalid request secret:' + str(content[0]))
        return

    data_in = json.loads(content[1])
    response = bot.handle_input(data_in)

    await message.reply(response)

# Start the bot using TOKEN
client.run(TOKEN)