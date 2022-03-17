# This handles the actual bot logic
####################################################################################################
from datetime import datetime
from distutils.command.config import config
from re import A
import sys
import discord

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger #pylint: disable=E0401
from lib.utils import Utils #pylint: disable=E0401

class Bot:


    def __init__(self, logger: Logger, config, client: discord.Client):
        self.logger = logger
        self.config = config
        self.client = client
        self.guild_id = 0


    async def send_tts(self, ctx, args):
        """Send tts message"""
        to_say = ' '.join(args)
        await ctx.guild.get_member(self.client.user.id).edit(nick=ctx.author.name)
        message = await ctx.send(to_say, tts=True)

        async def cleanupFunc(*args):
            message: discord.Message = args[0][0]
            await message.delete()

        # Calculate cleanup 
        # | 4.7 AvgWordLen * 100 AvgWordPerMin
        # | 470 Chars / 60 seconds
        padding = 8.0
        rate = 60.0/470.0
        time = (rate * len(to_say)) + padding

        Utils.future_call(time, cleanupFunc, [message])

        await ctx.guild.get_member(self.client.user.id).edit(nick=self.config['DEFAULT_NAME'])

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
