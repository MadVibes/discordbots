# This handles the actual bot logic
####################################################################################################
from datetime import datetime
from distutils.command.config import config
from fuzzywuzzy import process
import sys, time
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
        self.clip_list = {
                    "Augh":"augh.mp3",
                    "Aughhh":"aughhh.mp3",
                    "Bing Chilling":"bing_chilling.mp3",
                    "Bishcuish":"biscuits.mp3",
                    "Skedaddle":"bongo.mp3",
                    "Bonjour":"bonjour.mp3",
                    "Careless Whisper":"careless_whisper.mp3",
                    "Emotional Damage":"damage.mp3",
                    "Ding":"ding.mp3",
                    "What the dog doin":"dog.mp3",
                    "Dreamland":"kirby_dreamland.mp3",
                    "Ooo Friend":"friend.mp3",
                    "2 Hours later":"later.mp3",
                    "Oow":"minecraft.mp3",
                    "Noice":"noice.mp3",
                    "Noooo!":"noo.mp3",
                    "Oof":"oof.mp3",
                    "REEEE":"ree.mp3",
                    "Sod it":"sod_it.mp3",
                    "Wow":"wow.mp3",
                    "WTF yo doin?":"wtf.mp3",
                    "Yes please":"yes_please.mp3",
                    "Sleeper":"sleeper.mp3"
                }


    async def send_tts(self, ctx, args):
        """Send tts message"""
        to_say = ' '.join(args)
        await ctx.guild.get_member(self.client.user.id).edit(nick=ctx.author.name)
        self.logger.log(f'Playing TTS for {ctx.author.id}')
        try:
            message = await ctx.send(to_say, tts=True)
        except Exception as e:
            self.logger.error(f'Error sending tts message:')
            self.logger.error(e)
            return

        async def cleanupFunc(*args):
            message: discord.Message = args[0][0]
            await message.delete()

        # Calculate cleanup 
        # | 4.7 AvgWordLen * 100 AvgWordPerMin
        # | 60 seconds / 470 Chars (From above)
        padding = 8.0
        rate = 60.0/470.0
        time = (rate * len(to_say)) + padding

        Utils.future_call(time, cleanupFunc, [message])

        await ctx.guild.get_member(self.client.user.id).edit(nick=self.config['DEFAULT_NAME'])


    async def handle_sound(self, ctx, args):
        """Handles processing of sound"""
        if len(args) > 2:
            query = ' '.join(args[1:len(args)]) # Get query string by combining anything after 'play' (index 1)
        else:
            query = args[1] # Else, get only arguement after 'play'
        fuzzy = process.extract(query, self.clip_list.keys())
        matches = []
        for match in fuzzy:
            if match[1] > 90:
                matches.append(match[0])
        # Handle matches
        # 0 matches
        if len(matches) == 0:
            await ctx.reply('No sounds match that name')
            return
        # 1+ matches
        elif len(matches) > 1:
            items = []
            for item in matches:
                items.append(' \n - '+item)
            await ctx.reply('Sound play request was too generic, did you mean?' + ''.join(items))
            return
        # Play sound
        self.logger.log(f'Playing sound {matches[0]} for {ctx.author.id}')
        await self.play_sound(ctx, matches[0])


    async def play_sound(self, ctx, sound):
        """Handles playing of sound"""
        # Connect to VC and play audio
        if ctx.author.voice is not None:
            voice_channel = ctx.message.author.voice.channel
            active_voice = await voice_channel.connect()
            time.sleep(0.1)
            active_voice.play(discord.FFmpegPCMAudio(executable='ffmpeg',source=self.config['AUDIO_CLIP_DIR']+self.clip_list[sound]))
            # Wait until audio is finished and then leave the VC
            time.sleep(0.5)
            while active_voice.is_playing():
                time.sleep(0.15)
            time.sleep(0.1)
            await active_voice.disconnect()
        else:
            await ctx.reply('You\'re not in a channel!')


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
