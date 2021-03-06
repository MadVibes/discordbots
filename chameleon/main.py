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
from lib.shared import Shared #pylint: disable=E0401
from lib.emote_manager import CoinManager #pylint: disable=E0401
from lib.utils import Utils #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'chameleon'
config = configparser.ConfigParser()
config.read('./config/config.ini') # CHANGE ME
config = config[bot_type]
config.bot_type = bot_type
config.version = 'v1.2'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (534790879296)
intents = discord.Intents.default()
intents.members = True #pylint: disable=E0237
intents.messages = True #pylint: disable=E0237

logger = Logger(int(config['LOGGING_LEVEL']), config['WRITE_TO_LOG_FILE'], config['LOG_FILE_DIR'])
if ('LOGGING_PREFIX' in config and 'LOGGING_PREFIX_SIZE' in config):
    logger.custom_prefix = config['LOGGING_PREFIX']
    logger.custom_prefix_size = int(config['LOGGING_PREFIX_SIZE'])
logger.log(f'Starting {bot_type} - ' + config.version)

client = commands.Bot(command_prefix=config['COMMAND_PREFIX'], intents=intents)
cm = CoinManager(logger)
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
    # Load cogs
    client.add_cog(Shared(client, config))
    # Load CoinManager
    cm.set_guild(client.get_guild(bot.guild_id))
    async def initCM(*args):
        cm: CoinManager = args[0][0]
        await cm.populate_bot_emojis()
    time = 30 # Seconds
    Utils.future_call(time, initCM, [cm])


@client.command(name='tts')
async def command_tts(ctx: commands.Context, *args):
    """
    Execute tts command.
    Usage:
        tts [MESSAGE_TO_SAY]
    """

    user_balance = bank.get_balance(ctx.author.id)
    # insufficient balance
    if int(config['TTS_COST']) >= user_balance:
        await ctx.reply(f'Insufficient balance, current balance is {user_balance} {cm.currency()}')
        return
    # Perform tts and spend currency
    try:
        await bot.send_tts(ctx, args)
        bank.spend_currency(ctx.author.id, int(config['TTS_COST']))

    except Exception as e:
        logger.warn('Failed to execute tts:')
        logger.warn(str(e))

@client.command(name='sound')
async def command_sound(ctx: commands.Context, *args):
    """
    Play sounds in discord.
    Usage:
        sound list
        sound play [NAME]
        sound cost
        sound help
    """
    if len(args) == 0:
        await ctx.reply(f'Invalid command, see $sound help')
        return
    # Help menu
    elif args[0] == 'help':
        embed = discord.Embed(name='Sound Command help',
                description='-------',
                inline=True)
        embed.add_field(
                name='$sound list',
                value='List all possible sounds',
                inline=False)
        embed.add_field(
                name='$sound play [name]',
                value='Play a sound',
                inline=False)
        embed.add_field(
                name='$sound cost',
                value='Gets the cost to play a sound',
                inline=False)
        embed.add_field(
                name='$sound help',
                value='This menu',
                inline=False)
        await ctx.send(embed=embed)
        return
    elif args[0] == 'list':
        embed = discord.Embed(name='Sounds list',
                description='Available sounds to play, Current cost to play is ' + config['AUDIO_CLIP_COST'] + f' {cm.currency()}',
                inline=True)
        embed.add_field(
                name='\n'.join(bot.clip_list.keys()),
                value='E.g. $sound play Ding',
                inline=False)
        await ctx.send(embed=embed)
    elif args[0] == 'cost':
        await ctx.reply(f'Current cost is {config["AUDIO_CLIP_COST"]} {cm.currency()}')
        return
    elif args[0] == 'play':
        user_balance = bank.get_balance(ctx.author.id)
        if int(config['AUDIO_CLIP_COST']) >= user_balance:
            await ctx.reply(f'Insufficient balance, current balance is {user_balance} {cm.currency()}')
            return
        # Start handling of sound command
        try:
            await bot.handle_sound(ctx, args)
            bank.spend_currency(ctx.author.id, int(config['AUDIO_CLIP_COST']))
            return

        except Exception as e:
            logger.warn('Failed to handle sound:')
            logger.warn(str(e))
            return
    else:
        await ctx.reply('You have reached the world\'s edge, none but devils play past here\nInvalid command, see $sound help')
        return


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
