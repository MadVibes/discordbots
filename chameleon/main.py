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
from lib.utils import Utils
from lib.logger import Logger
from lib.bank_interface import Bank
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

@client.command(name='tts')
async def command_tts(ctx: commands.Context, *args):
    """Execute tts command""" 

    user_balance = bank.getBalance(ctx.author.id)
    # insufficient balance
    if int(config['TTS_COST']) >= user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} vbc')
        return
    # Perform tts and spend currency
    try:
        await bot.send_tts(ctx, args)
        bank.spendCurrency(ctx.author.id, int(config['TTS_COST']))

    except Exception as e:
        logger.warn('Failed to execute tts:')
        logger.warn(str(e))

@client.command(name=' ', aliases=config['IGNORE_COMMANDS'].split(','))
async def command_nothing(ctx: commands.Context, *args):
    """"""# Catch to do nothing. Used for overlapping bot prefix

# Start the bot using TOKEN
client.run(TOKEN)