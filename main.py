import os 
import sys
import datetime
import discord
from discord.ext import tasks

@tasks.loop(minutes = 30)
async def bumpcheck(overseer):
  role_id = 1240350374544543818
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
      return 

    interaction = message.interaction
    if not interaction:
      continue 
        
    if interaction.name == "bump" and message.author.id == 302050872383242240:
      latest_bump = message      
      break
    
  if not latest_bump: 
    print("bumpcheck() : failed to retrieve latest bump message!")
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
  if sys.argv[1]:
    return sys.argv[1]
  token = os.getenv('OVERSEERTOKEN', "UNDEFINED")
  if token == "UNDEFINED":
    print("Failed to retrieve the token. Exiting the application.")
    exit()  
  else:
    print("Token is retrieved successfully.")
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
