# Croupier Bot
# Handles Gambling
####################################################################################################
import discord
import os, sys, json
import configparser
import discord
from discord.ext import commands

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.utils import Utils #pylint: disable=E0401
from lib.logger import Logger #pylint: disable=E0401
from lib.bank_interface import Bank #pylint: disable=E0401
from lib.shared import Shared #pylint: disable=E0401
from lib.emote_manager import CoinManager, ScratchManager #pylint: disable=E0401
from lib.utils import Utils #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'croupier'
config = configparser.ConfigParser()
config.read('./config/config.ini') # CHANGE ME
config = config[bot_type]
config.bot_type = bot_type
config.version = 'v1.5'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (534790879296)
intents = discord.Intents.default()
#intents.members = True
#intents.messages = True

logger = Logger(int(config['LOGGING_LEVEL']), config['WRITE_TO_LOG_FILE'], config['LOG_FILE_DIR'])
if ('LOGGING_PREFIX' in config and 'LOGGING_PREFIX_SIZE' in config):
    logger.custom_prefix = config['LOGGING_PREFIX']
    logger.custom_prefix_size = int(config['LOGGING_PREFIX_SIZE'])
logger.log(f'Starting {bot_type} - ' + config.version)

client = commands.Bot(command_prefix=config['COMMAND_PREFIX'], intents=intents)
bank = Bank(logger, config)
cm = CoinManager(logger)
sm = ScratchManager(logger)
bot = Bot(logger, config, bank, client, cm, sm)


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
    # Load ScratchManager
    sm.set_guild(client.get_guild(bot.guild_id))
    await sm.try_add_emojis(config['EMOJI_SOURCE'])


@client.command(name='bet')
async def bet(ctx: commands.Context, *args):
    """
    Create and join bets.
    Usage:
        bet
        bet create [NAME]
        bet for|against [ID] [WAGER]
        bet help

    See pay command for payouts
    """
    await bot.bet(ctx, args)


@client.command(name='pay')
async def pay(ctx, arg, arg2=None):
    """
    Pay out a bet.
    Usage:
        pay [ID] for|against|stalematea
        pay help
    """
    await bot.pay(ctx, arg, arg2)


@client.command(name='deathroll')
@commands.guild_only()
async def deathroll(ctx, arg=None, arg2=None):
    """
    Create and join deathrolls.
    Usage:
        deathroll
        deathroll create [WAGER]
        deathroll join [ID]
        deathroll start [ID]
        deathroll delete [ID]
        deathroll help
    """
    await bot.deathroll(ctx, arg, arg2)


@client.command(name='scratchcard')
@commands.guild_only()
async def scratchcard(ctx, arg=None, arg2=None):
    """
    Purchase and use a scratchcard.
    Usage:
        scratchcard buy [WAGER]
        scratchcard help
    """
    try:
        await bot.scratchcard(ctx, arg, arg2)
    except Exception as e:
        logger.error('Failed to handle Scratchcard:')
        logger.error(str(e))


@client.command(name='slots')
@commands.guild_only()
async def slots(ctx, *args):
    """
    Purchase to play on the slot machine.
    Usage:
        slots spin [WAGER]
        slots help
    """
    try:
        if args[0].lower() == "spin":
            if args[1].isdigit():
                if int(args[1]) > 10:
                    await bot.play_slots(ctx, int(args[1]))
                else:
                    await ctx.message.add_reaction('❌')
                    await ctx.send("Wagers must be over 10 VBC")
            else:
                await ctx.message.add_reaction('❌')
        
        elif args[0].lower() == "help":
            await bot.help_embed(ctx, "slots")

    except Exception as e:
        logger.error('Failed to handle Scratchcard:')
        logger.error(str(e))


@client.command(name='ng')
@commands.guild_only()
async def numberguesser(ctx, arg=None):
    """
    Purchase and play Number Guesser.
    Usage:
        ng start Costs: 90 VBC
        ng help
    """
    try:
        await bot.NG_start(ctx, arg)
    except Exception as e:
        logger.error('Failed to handle Number guesser:')
        logger.error(str(e))

# Start the bot using TOKEN
client.run(TOKEN)

########################################################################################################
#   Copyright (C) 2022  Liam Coombs, Sam Tipper, Rhydian Davies
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
