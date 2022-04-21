# Shared lib to implement common functions between bots
#
########################################################################################################
from discord.ext import commands
from discord.ext.commands import Bot

class Shared(commands.Cog):


    def __init__(self, bot: Bot, config):
        self.config = config
        self.bot = bot

        @bot.command(name=' ', aliases=self.config['IGNORE_COMMANDS'].split(','))
        async def shared_nothing(ctx, *args):
            """"""# Handle ignoring commands from other bots


    @commands.command(name='version')
    async def shared_version(self, ctx: commands.Context, *args):
        """View bot version"""
        if len(args) == 0 or args[0] == self.config.bot_type:
            await ctx.message.reply(self.config.version)
