# Bank Bot
# Handles the moving/maintaining of VibeCoin
####################################################################################################
import discord
import os, sys, json, math, configparser
from fuzzywuzzy import process
from discord.ext import tasks
from discord.ext import commands

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.server import Web_Server #pylint: disable=E0401
from bot import Bot

# CONFIGS/LIBS
########################################################################################################
bot_type = 'bank'
config = configparser.ConfigParser()
config.read('./config.ini') # CHANGE ME
config = config[bot_type]

VERSION = 'v1.0'

TOKEN = config['DISCORD_TOKEN']
GUILD = config['DISCORD_GUILD']
########################################################################################################

# Bot perms (534790879296)
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

    # Start loops
    balance_accrue.start()
    balance_fade.start()
    # Create it's own user in bank
    if not bot.user_id_exists(client.user.id):
        bot.create_user(client.user.id, client.user.name)
    # Tax account creation
    if not(bot.user_id_exists(int(config['TAX_ACCOUNT_ID']))):
        success = bot.create_user(int(config['TAX_ACCOUNT_ID']), 'TAX_ACCOUNT')
        if not(success):
            logger.warn('Failed to create new user TAX_ACCOUNT')
    # Restore defaults
    await client.get_guild(bot.guild_id).get_member(client.user.id).edit(nick=config['DEFAULT_NAME'])
    if config['STATUS_START_ONLINE'] == 'True':
        await client.change_presence(status=discord.Status.online)
    else:
        await client.change_presence(status=discord.Status.invisible)


@client.event
async def on_message(message: discord.Message):
    # If the user does not exist, add them to DB
    if not(bot.user_id_exists(int(message.author.id))):
        success = bot.create_user(int(message.author.id), message.author.display_name)
        if not(success):
            logger.warn(f'Failed to create new user {message.author.display_name}')

    # Handle normal on_message event
    await client.process_commands(message)


@tasks.loop(minutes=float(config['BALANCE_ACCRUE_TIME']))
async def balance_accrue():
    """Accrue balance to users currently in a channel"""
    online_users = []

    guild: discord.Guild = client.get_guild(bot.guild_id)
    for channel in guild.voice_channels:
        # Skip afk channel
        if channel.name != guild.afk_channel.name:
            for member in channel.members:
                # Skip giving coin on conditions
                #   1. deafened
                #   2. only 1 person in channel
                #   3. is another bot
                if not(member.voice.self_deaf
                    or len(channel.members)==1
                    or member.bot):
                    online_users.append(member)

    for online_user in online_users:
        if not(bot.user_id_exists(int(online_user.id))):
            bot.create_user(int(online_user.id), online_user.display_name)
        bot.alter_balance(int(config['BALANCE_ACCRUE']), online_user.id)
        logger.debug(f"Accrue balance for {online_user.display_name}")


@tasks.loop(minutes=float(config['BALANCE_FADE_TIME']))
async def balance_fade():
    """Fade balance to users currently in a channel and afk"""
    afk_users = []

    guild: discord.Guild = client.get_guild(bot.guild_id)

    for channel in guild.voice_channels:
        # Skip afk channel
        if channel.name != guild.afk_channel.name:
            for member in channel.members:
                # fade coin on conditions
                #   1. deafened
                if member.voice.self_deaf:
                    afk_users.append(member)
        # Afk channel
        else:
            for member in channel.members:
                afk_users.append(member)

    for afk_user in afk_users:
        if not(bot.user_id_exists(int(afk_user.id))):
            bot.create_user(int(afk_user.id), afk_user.display_name)
        bot.alter_balance(-int(config['BALANCE_FADE']), afk_user.id)
        logger.debug(f"Fade balance for {afk_user.display_name}")


@client.command(name='balance')
async def command_balance(ctx: commands.Context, *args):
    """Display a users balance, or a target users balance"""
    if not(bot.user_id_exists(int(ctx.author.id))):
        bot.create_user(int(ctx.author.id), ctx.author.display_name)

    # No target user specified
    if len(args) == 0:
        balance = bot.get_balance(ctx.author.id)
        await ctx.send(f'Your current balance is {balance} VBC')

    # A target was specified
    else:
        guild: discord.Guild = client.get_guild(bot.guild_id)
        all_members = guild.members
        all_member_names = list(map(lambda member: member.display_name, all_members))
        fuzzy = process.extract(args[0], all_member_names)
        matches = []
        for match in fuzzy:
            if match[1] > 95:
                matches.append(match[0])
        # Handle matches
        # 0 matches
        if len(matches) == 0:
            await ctx.reply('No users match that name')
            return
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await ctx.reply('User was too generic, did you mean?' + ''.join(items))
            return
        target_id = -1
        for member in all_members:
            if member.display_name == matches[0]:
                target_id = member.id
                break
        balance = bot.get_balance(target_id)
        await ctx.send(f'{matches[0]} current balance is {balance} VBC')


@client.command(name='leaderboard')
async def command_leaderboard(ctx: commands.Context, *args):
    """Display a leaderboard"""
    if not(bot.user_id_exists(int(ctx.author.id))):
        bot.create_user(int(ctx.author.id), ctx.author.display_name)

    guild: discord.Guild = client.get_guild(bot.guild_id)
    all_members = guild.members
    leaderboard = {}
    # Populated leaderboard data
    for member in all_members:
        if len(leaderboard.keys()) >= 10:
            break
        if member.id == client.user.id or member.bot:
            continue
        balance = bot.get_balance(member.id)
        if balance is None:
            continue
        if balance == 0:
            continue
        if balance in leaderboard:
            leaderboard[balance].append(member.display_name)
        else:
            leaderboard[balance] = [member.display_name]
    # Create and populate embed
    embed = discord.Embed(title='**VibeCoin Leaderboard**', colour=discord.Colour.gold())
    for key in sorted(leaderboard, reverse=True):
        embed.add_field(name=f'{key} VBC', value=f'{", ".join(leaderboard[key])}', inline=False)
    await ctx.send(embed=embed)


@client.command(name='transfer')
async def command_transfer(ctx: commands.Context, *args):
    """Tansfer money to another player"""


@client.command(name='version')
async def command_tts(ctx: commands.Context, *args):
    """View bot version"""
    if len(args) == 0 or args[0] == bot_type:
        await ctx.message.reply(VERSION)


@client.command(name=' ', aliases=config['IGNORE_COMMANDS'].split(','))
async def command_nothing(ctx: commands.Context, *args):
    """"""# Catch to do nothing. Used for overlapping bot prefix


# WEB SERVER INIT
########################################################################################################

# Mini service/class for actions
class Servlet:
    def __init__(self, client: discord.Client, bot: Bot):
        self.client = client
        self.bot = bot


# Functions for webserver
def getBalance(service: Servlet, parameters: json):
    """Return users balance"""
    if 'user_id' not in parameters:
        raise Exception('user_id was not included in parameters')

    return service.bot.req_get_balance(user_id=parameters['user_id'])


def moveCurrency(service: Servlet, parameters: json):
    """Move balance from one user to another"""
    if ('user_id_sender' not in parameters
        or 'user_id_receiver' not in parameters
        or 'amount' not in parameters):
        raise Exception('user_id_sender, user_id_receiver, amount were not all included in parameters')

    return service.bot.req_move_currency(user_id_sender=parameters['user_id_sender'], user_id_receiver=parameters['user_id_receiver'], amount=parameters['amount'])


def spendCurrency(service: Servlet, parameters: json):
    """Spend balance of user"""
    if ('user_id' not in parameters
        or 'amount' not in parameters):
        raise Exception('user_id, amount were not all included in parameters')

    return service.bot.req_move_currency(user_id_sender=parameters['user_id'], user_id_receiver=service.client.user.id, amount=parameters['amount'])


def withdrawCurrency(service: Servlet, parameters: json):
    """Withdraw balance of bank"""
    if ('user_id' not in parameters
        or 'amount' not in parameters):
        raise Exception('user_id, amount were not all included in parameters')

    return service.bot.req_move_currency(user_id_sender=service.client.user.id, user_id_receiver=parameters['user_id'], amount=parameters['amount'])


def spendCurrencyTaxed(service: Servlet, parameters: json):
    """Spend balance of user, split amount into tax account based on band"""
    if ('user_id' not in parameters
        or 'amount' not in parameters
        or 'tax_band' not in parameters):
        raise Exception('user_id, amount, tax_band were not all included in parameters')

    tax_amount = math.floor(parameters['amount'] * float(service.bot.tax_bands[parameters['tax_band']])/100)
    bank_amount = int(parameters['amount']) - tax_amount
    service.bot.req_move_currency(user_id_sender=parameters['user_id'], user_id_receiver=int(service.bot.config['TAX_ACCOUNT_ID']), amount=tax_amount)

    return service.bot.req_move_currency(user_id_sender=parameters['user_id'], user_id_receiver=service.client.user.id, amount=bank_amount)


def withdrawCurrencyTaxed(service: Servlet, parameters: json):
    """Withdraw balance of bank, split amount but don't pay tax account based on band. PLEASE READ CODE COMMENT FOR withdrawCurrencyTaxed IN bank/main.py """
    if ('user_id' not in parameters
        or 'amount' not in parameters
        or 'tax_band' not in parameters):
        raise Exception('user_id, amount, tax_band were not all included in parameters')

    tax_amount = math.floor(parameters['amount'] * float(service.bot.tax_bands[parameters['tax_band']])/100)
    bank_amount = int(parameters['amount']) - tax_amount
    # NOTE(Liam):
    #   This is a hard one to think about. So when withdrawing with a tax rate, we need to give a user restricted amount. But we need to be smart when moving money from bank -> tax.
    #   This could result in a scenarion with the bank has a net loss from it's total funds and the tax account has a net gain.
    #   for example:
    #       User1 + User2 spend 1000 in total on a wager that is taxed 10%.
    #       this means +900 for Bank account, and +100 for Tax account
    #       When User1 wins, a taxable currency withdraw is made of 1000. (900 to user, 100 to tax)
    #       This ends in a scenario with:
    #          +900 for User 1  (CORRECT)
    #          +200 for Tax     (INCORRECT: should be +100 as it should not be taxed inbound and outbound)
    #          -100 for Bank    (INCORRECT: should be ~0 as the bank should only be holding the balance temporarily during the bet)
    #       The correct end scenario should be
    #          +900 for User 1 
    #          +100 for Tax
    #          +/- 0 for Bank
    #   To work around this issue, the current line below is commented out.
    #   A real solution to the issue is for the service that is actually calling the withdraw function to calculate the amount to move post tax before ever calling this function via
    #   the bank interface. Then there should be a call in the bank lib to get the current tax rates for a given band so that it is dynamic, and tax rates are controlled centrally 
    #   by the bank bot.
    #service.bot.req_move_currency(user_id_sender=service.client.user.id, user_id_receiver=int(service.bot.config['TAX_ACCOUNT_ID']), amount=tax_amount)

    return service.bot.req_move_currency(user_id_sender=service.client.user.id, user_id_receiver=parameters['user_id'], amount=bank_amount)

# Mapping of possible functions that the web server can call
actions = {
    'getBalance': getBalance,
    'moveCurrency': moveCurrency,
    'spendCurrency': spendCurrency,
    'withdrawCurrency': withdrawCurrency,
    'spendCurrencyTaxed': spendCurrencyTaxed,
    'withdrawCurrencyTaxed': withdrawCurrencyTaxed
}
servlet = Servlet(client, bot)

web = Web_Server(logger, actions, servlet, config)
web.start()

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
