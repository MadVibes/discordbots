# Shared lib to implement common functions between bots
#
########################################################################################################
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.ext.commands import Bot

class Shared(commands.Cog):


    def __init__(self, client, config):
        self.config = config
        self.client = client

        # Load custom help command handler
        client.help_command = MaskingHelpCommand(config, no_category = 'Commands')

        @client.command(name=f'{self.config.bot_type.lower()}', hidden=True)
        async def bot_help(ctx):
            """"""

        if 'IGNORE_COMMANDS' in self.config:
            @client.command(name='DONOTREPLY', aliases=self.config['IGNORE_COMMANDS'].split(','), hidden=True)
            async def shared_nothing(ctx, *args):
                """"""# Handle ignoring commands from other bots


    @commands.command(name='version')
    async def shared_version(self, ctx: commands.Context, *args):
        """
        View bot version
        Usage:
            version
            version [BOT_TYPE]
        """
        if len(args) == 0 or args[0] == self.config.bot_type:
            await ctx.message.reply(f'{self.config.version} - {self.config.bot_type.upper()}')


class MaskingHelpCommand(commands.DefaultHelpCommand):


    def __init__(self, config, *args, **kwargs):
        self.bot_config = config
        super(MaskingHelpCommand, self).__init__(*args, **kwargs)


    async def send_command_help(self, command):
        """
        Override standard command handling.
        If command name is 'DONOTEREPLY', do nothing!
        """
        if command.name == 'DONOTREPLY':
            return
        elif command.name == self.bot_config.bot_type.lower():
            await self.send_bot_help((None,[]))
        else:
            await super(MaskingHelpCommand, self).send_command_help(command)


    async def send_error_message(self, error):
        # Command not found, error does not have a type, its just a string
        if 'No command called' in error:
            return
        else:
            await super(MaskingHelpCommand, self).send_error_message(error)


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
