# This handles the actual bot logic
####################################################################################################
import sys
import discord
import re

sys.path.insert(0, '../')
sys.path.insert(0, './')
from lib.logger import Logger
from lib.data import Database

db_schema = {
  "polls": [],
  "voting on": [0, 0, 0],
}


class Bot:
  def __init__(self, logger: Logger, config, bank, client: discord.Client):
    self.logger = logger
    self.config = config
    self.client = client
    self.bank = bank
    self.data = Database(self.logger, self.config['DATA_STORE'], db_schema)

  
  async def poll_help(self, ctx):
    embed = discord.Embed(
      title='Polling Help',
      description='-----',
      colour=discord.Colour.blue()
    )
    embed.add_field(name='$poll', value='Shows all active polls.' ,inline=False)
    embed.add_field(name='$poll create [title]', value='Creates a poll with a custom title.' ,inline=False)
    embed.add_field(name='$poll [id]', value='Shows a poll to either vote on or close.' ,inline=False)

    await ctx.send(embed=embed)

    
  async def reaction(self, reaction, user):
    data = self.data.read()
    if not user.bot:
      await reaction.remove(user)
      if data['voting on'][0] == reaction.message.id:
        ID = int(data['voting on'][1])
        if reaction.emoji == '✅':
          if user.id not in data['polls'][ID]['user_ids']:
            data['polls'][ID]['for'].append(user.id)
            data['polls'][ID]['user_ids'].append(user.id)
            self.data.write(data)
          elif user.id not in data['polls'][ID]['against']:
            pos = data['polls'][ID]['for'].index(user.id)
            data['polls'][ID]['for'].pop(pos)
            pos2 = data['polls'][ID]['user_ids'].index(user.id)
            data['polls'][ID]['user_ids'].pop(pos2)
            self.data.write(data)
          await self.get_context(data['voting on'][0], int(data['voting on'][1]), data['voting on'][2], 1)
          
        elif reaction.emoji == '❌':
          if user.id not in data['polls'][ID]['user_ids']:
            data['polls'][ID]['against'].append(user.id)
            data['polls'][ID]['user_ids'].append(user.id)
            self.data.write(data)
          elif user.id not in data['polls'][ID]['for']:
            pos = data['polls'][ID]['against'].index(user.id)
            data['polls'][ID]['against'].pop(pos)
            pos2 = data['polls'][ID]['user_ids'].index(user.id)
            data['polls'][ID]['user_ids'].pop(pos2)
            self.data.write(data)
          await self.get_context(data['voting on'][0], int(data['voting on'][1]), data['voting on'][2], 1)
          
        elif reaction.emoji == '🗑️':
          if user.id == data['polls'][ID]['initiator']:
            active_poll = await self.get_active_poll(ID, data)
            if active_poll != None:
              await self.get_context(data['voting on'][0], int(data['voting on'][1]), data['voting on'][2], 2)
          
    
  async def get_active_poll(self, ID, data):
    active_poll = None
    for poll in data['polls']:
      if poll['ID'] == int(ID):
        active_poll = poll
        break
    if active_poll != None:
      return active_poll
    else:
      return None

  
  async def all_polls_embed(self, ctx):
    data = self.data.read()
    embed = discord.Embed(
      title='All Active Polls',
      description='-----',
      colour=discord.Colour.blue()
    )
    if data['polls'] != db_schema['polls']:
      for i in data["polls"]:
        id = i['ID']
        title = str(i['title'])
        title = re.sub("[,'\[\]]", "", title)
        fors = len(i['for'])
        against = len(i['against'])

        complete = f"**Title:** \n {title.title()} \n" + f"**For:** \n {fors}\n" + f"**Against:** \n {against}"

        embed.add_field(name=f'Poll ID: {id}', value=f'{complete}' ,inline=True)
        
    else:
      embed.add_field(name='No polls :(', value='What are you waiting for? Create a poll dummy!' ,inline=True)
      
    await ctx.send(embed=embed)

  
  async def get_context(self, msg_id, ID, channel_id, state):
    channel = await self.client.fetch_channel(int(channel_id))
    track_id = await channel.fetch_message(int(msg_id))
    ctx = await self.client.get_context(track_id)
    if state == 1:
      await self.poll_embed(ctx, ID, 1)
    elif state == 2:
      await self.poll_embed(ctx, ID, 2)


  async def poll_embed(self, ctx, ID, state):
    data = self.data.read()
    active_poll = await self.get_active_poll(ID, data)
    if active_poll != None:
      title = active_poll['title']
      fors = active_poll['for']
      against = active_poll['against']
      title = re.sub("[,'\[\]]", "", str(title))

      if len(fors) > len(against):
        colour = discord.Colour.blue()
      else:
        colour = discord.Colour.red()

      embed = discord.Embed(
        title=f'{title.title()}',
        description=f'**Poll ID**: {ID}\nVote not registering? Type: $poll {ID}',
        colour=colour
      )
      if fors and against:
        for_len = len(fors)
        against_len = len(against)
        total_len = for_len + against_len
        perc_for = str(round(for_len / total_len * 100)) + "%"
        perc_against = str(round(against_len / total_len * 100)) + "%"
      else:
        perc_for = ""
        perc_against = ""
        
      if fors:
        complete_users_for = ""
        for user in fors:
          user = f"<@{user}>\n"
          complete_users_for = complete_users_for + user
        embed.add_field(name='FOR THIS NOTION:', value=f'{complete_users_for} {perc_for}' ,inline=True)
      else:
        embed.add_field(name='FOR THIS NOTION:', value='*cricket sounds*\nI guess no one here.' ,inline=True)

      if against:
        complete_users_against = ""
        for user in against:
          user = f"<@{user}>\n"
          complete_users_against = complete_users_against + user
        embed.add_field(name='AGAINST THIS NOTION:', value=f'{complete_users_against} {perc_against}' ,inline=True)
      else:
        embed.add_field(name='AGAINST THIS NOTION:', value='*cricket sounds*\nI guess no one here.' ,inline=True)

      if state == 0:
        embed.set_footer(text="Open\nClick the bin emoji to close votes.")
        msg = await ctx.send(embed=embed)
        data['voting on'][0] = msg.id
        data['voting on'][1] = ID
        data['voting on'][2] = ctx.channel.id
        self.data.write(data)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        await msg.add_reaction('🗑️')
      elif state == 1:
        embed.set_footer(text="Open\nClick the bin emoji to close votes.")
        channel = await self.client.fetch_channel(data['voting on'][2])
        msg = data['voting on'][0]
        msg = await channel.fetch_message(msg)
        await msg.edit(embed=embed)
      elif state == 2:
        channel = await self.client.fetch_channel(data['voting on'][2])
        msg = data['voting on'][0]
        msg = await channel.fetch_message(msg)
        del data['polls'][ID]
        data['voting on'][0] = 0
        data['voting on'][1] = 0
        data['voting on'][2] = 0
        self.data.write(data)
        embed.set_footer(text="Closed")
        await msg.edit(embed=embed)
        
        
  async def make_poll(self, ctx, args, pro, against):
    data = self.data.read()
    length = len(data["polls"])
    while length in data["polls"]:
      length += 1

    poll_obj = {
      "ID": length,
      "title": args,
      "for": pro,
      "against": against,
      "user_ids": [],
      "initiator": ctx.author.id
    }
    
    data["polls"].append(poll_obj)
    self.data.write(data)
    return length

  
  async def poll(self, ctx, args):
    if not args:
      await self.all_polls_embed(ctx)

    elif args[0].isdigit():
      await self.poll_embed(ctx, args[0], 0)

    elif args[0].lower() == "help":
      await self.poll_help(ctx)
      
    elif args[0].lower() == "create":
      args = list(args)
      args.pop(0)
      pro = []
      against = []
      ID = await self.make_poll(ctx, args, pro, against)
      await self.poll_embed(ctx, ID, 0)
      