# Lib to handle emoji functions
# Includes child classes for specific scenarios
#
########################################################################################################
from lib.logger import Logger #pylint: disable=E0401
from discord import Guild
from io import BytesIO


class EmoteManager:


    def __init__(self, logger: Logger):
        self.use_emoji = False
        self.logger = logger
        self.active_emojis = {}
        self.custom_emojis = []


    def set_guild(self, guild: Guild):
        """Set guild after init"""
        self.guild = guild


    async def try_add_emojis(self, emoji_source):
        """Attempts to add bot emojis"""
        bot_emojis = self.custom_emojis
        all_emojis = []
        all_emojis_string = []
        for emoji in await self.guild.fetch_emojis():
            all_emojis.append(emoji)
            all_emojis_string.append(emoji.name)
        # Clean up existing emojis
        for emoji in bot_emojis:
            if emoji in all_emojis_string:
                to_remove = EmoteManager.get_emoji_from_name(emoji, all_emojis)
                await to_remove.delete()
        # Attempt to insert emoji
        for emoji in bot_emojis:
            with open(f'{emoji_source}/{emoji}' + (".gif" if '_ANIM' in emoji else ".png"), 'rb') as image:
                try:
                    created_emoji = await self.guild.create_custom_emoji(name=emoji, image=BytesIO(image.read()).getvalue(), reason='Bot Bank Emojis')
                    self.active_emojis[created_emoji.name] = created_emoji.id
                except Exception as e:
                    self.logger.error(f'Failed to insert emoji: {emoji}')
                    self.logger.error(e)
                    return
        self.use_emoji = True


    async def populate_bot_emojis(self):
        """If created emoji data is empty, populate it"""
        all_emojis = []
        for emoji in await self.guild.fetch_emojis():
            all_emojis.append(emoji)
        for emoji in self.custom_emojis:
            found_emoji = EmoteManager.get_emoji_from_name(emoji, all_emojis)
            self.active_emojis[found_emoji.name] = found_emoji.id
        self.use_emoji = True
        self.logger.debug('Loaded emojis!')


    @staticmethod
    def get_emoji_from_name(name: str, all_emojis):
        """Gets emoji from emojis list using name string"""
        for emoji in all_emojis:
            if emoji.name == name:
                return emoji
        return None


# Some class inheritance for handling different scenarios
class CoinManager(EmoteManager):


    def __init__(self, logger: Logger):
        super().__init__(logger)
        self.custom_emojis = ['VBC', 'VBC_ANIM']


    def currency(self, animated=False):
        """Returns currency string"""
        if not self.use_emoji:
            return 'VBC'
        if len(self.active_emojis) == 0:
            self.logger.error('Bot emojis have not be loaded, try calling populate_bot_emojis()')
            exit(1)
        if animated:
            return '<a:VBC_ANIM:' + str(self.active_emojis['VBC_ANIM']) + '>'
        else:
            return '<:VBC:' + str(self.active_emojis['VBC']) + '>'



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
