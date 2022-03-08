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

    async def send_tts(self, ctx, args):
        """Send tts message"""
        to_say = ' '.join(args)
        await ctx.guild.get_member(self.client.user.id).edit(nick=ctx.author.name)
        message = await ctx.send(to_say, tts=True)
        await message.delete()
        await ctx.guild.get_member(self.client.user.id).edit(nick=self.config['DEFAULT_NAME'])

########################################################################################################
#   Copyright (C) 2022  Liam Coombs
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
