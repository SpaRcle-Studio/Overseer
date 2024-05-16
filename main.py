import os 
import sys
import argparse
import datetime
import discord
from discord.ext import tasks

@tasks.loop(minutes = 5)
async def bumpcheck(overseer):
  role_id = 1240350374544543818
  remind_needed = True
  if not overseer:
    print("bumpcheck() : client object is not valid!")
    return

  bump_channel = overseer.get_channel(1218867028304072755)
  if not bump_channel: 
    print("bumpcheck() : channel object is not valid!")
    return 

  latest_bump = None
  async for message in bump_channel.history(limit=200):
    if message.author.id == 1240293764837277736:
      remind_needed = False

    interaction = message.interaction
    if not interaction:
      continue 
        
    if interaction.name == "bump" and message.author.id == 302050872383242240 and remind_needed:
      latest_bump = message      
      break
    
  if not latest_bump: 
    print("bumpcheck() : failed to retrieve latest needed bump message!")
    return 

  now = datetime.datetime.now(datetime.timezone.utc)
  difference = now - message.created_at
  difference_in_s = difference.total_seconds()
  hours = divmod(difference_in_s, 3600)[0]
  if hours > 2:
    await bump_channel.send(f"Time to bump the server! :) ||<@&{role_id}>||")

class Overseer(discord.Client):
  async def on_ready(self):
    print(f'Logged in as {self.user} (ID: {self.user.id})')
    print('------')
    bumpcheck.start(self)

    #async def on_member_join(self, member):
    #    guild = member.guild
    #    if guild.system_channel is not None:
    #        to_send = f'Welcome {member.mention} to {guild.name}!'
    #        await guild.system_channel.send(to_send)

def initializeIntents():
  intents = discord.Intents.default()
  intents.members = True
  intents.typing = True
  intents.presences = True
  intents.message_content = True
  return intents 

def getToken():
  print("getToken() : trying to get token from command line arguments...")
  parser = argparse.ArgumentParser("SpaRcle Overseer")
  parser.add_argument("-token", help="Provide the token for the bot.", type=str, required=False, default="UNDEFINED")
  args = parser.parse_args() 
  if args.token != "UNDEFINED":
    print("getToken() : token is successfully retrieved.")
    return args.token
  print("getToken() : trying to get token from environment variables...")
  token = os.getenv('OVERSEERTOKEN', "UNDEFINED")
  if token == "UNDEFINED":
    print("getToken() : failed to retrieve the token. Exiting the application.")
    exit()  
  else:
    print("getToken() : token is retrieved successfully.")
    return token 

if __name__ == "__main__":
   print("Welcome to SpaRcle Overseer.")
   print("Trying to get the token from environment variables...")
   token = getToken()
   intents = initializeIntents()
   overseer = Overseer(intents=intents)
   print("Connecting to Discord API...")
   overseer.run(token) 
else:
   print("SpaRcle Overseer bot can only be ran directly.")
