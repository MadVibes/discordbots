# This handles the actual bot logic
####################################################################################################
from datetime import datetime
from distutils.command.config import config
from re import A
import sys
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger

class Bot:

    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client
        self.guild_id = 0

    async def can_afford(self):
        """Can user afford TTS message. returns true|false"""
        bank = self.client.get_user(int(self.config['COMMS_TARGET']))

        # await dms.send('TEst!')

    async def send_tts(self, ctx, args):
        """Send tts message"""
        to_say = ' '.join(args)
        await ctx.guild.get_member(self.client.user.id).edit(nick=ctx.author.name)
        message = await ctx.send(to_say, tts=True)
        await message.delete()
        await ctx.guild.get_member(self.client.user.id).edit(nick=self.config['DEFAULT_NAME'])
