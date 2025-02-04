import os
import sys
import sqlite3
import argparse
import datetime
import discord
from discord.ext import tasks, commands
from discord import app_commands
from discord.utils import get

@tasks.loop(minutes = 5)
async def bumpcheck(overseer):
  role_id = 1240350374544543818
  remind_message = f"Time to bump the server! :) ||<@&{role_id}>||"
  if not overseer:
    print("bumpcheck() : client object is not valid!")
    return

  bump_channel = overseer.get_channel(1218867028304072755)
  if not bump_channel:
    print("bumpcheck() : channel object is not valid!")
    return

  latest_bump = None
  print("bumpcheck() : checking if remind is needed...")
  async for message in bump_channel.history(limit=200):
    if message.author.id == 1240293764837277736 and message.content == remind_message:
      print("bumpcheck() : remind is not needed, exiting the loop.")
      return

    interaction = message.interaction
    if not interaction:
      continue

    if interaction.name == "bump" and message.author.id == 302050872383242240:
      latest_bump = message
      break

  if not latest_bump:
    print("bumpcheck() : failed to retrieve latest needed bump message!")
    return

  print(f"bumpcheck() : successfully retrieved latest needed bump message. It was created at: '{message.created_at}'.")

  now = datetime.datetime.now(datetime.timezone.utc)
  difference = now - message.created_at
  difference_in_s = difference.total_seconds()
  minutes = divmod(difference_in_s , 60)[0]
  print(f"bumpcheck() : the difference between current time and the latest bump is '{minutes}' minutes. Left till next remind: '{120-minutes}'")
  if minutes > 120:
    print("bumpcheck() : sending a remind message...")
    await bump_channel.send(remind_message)


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

print("Welcome to SpaRcle Overseer.")
print("Trying to get the token from environment variables...")
token = getToken()
intents = discord.Intents.all()
overseer = discord.Client(command_prefix="*", intents=intents)
tree = app_commands.CommandTree(overseer)

@tree.command(name="bumpstat", description="Tells you how many times you /bumped the server.", guild=discord.Object(id=768652124204433429))
async def bumpstat(interaction):
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  db_path = os.path.join(BASE_DIR, "overseerBumps.db")
  print(f"bumpstat() : trying to open connection. Path: '{db_path}'.")
  with sqlite3.Connection(db_path) as connection:
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)")
    connection.commit()
    print(f"bumpstat() searching for user with id: '{interaction.user.id}'.")
    cursor.execute("SELECT * FROM BumpCount WHERE userId = ?", [str(interaction.user.id)])
    row = cursor.fetchone()
    if row is None:
      await interaction.response.send_message("You have never /bump'ed the server yet. Good luck next time!")
    else:
      await interaction.response.send_message(f"```You have /bump'ed the server '{row[1]}' times!```")

@tree.command(name="leaderboard", description="Leaderboard of server's /bump'ers.", guild=discord.Object(id=768652124204433429))
async def leaderboard(interaction):
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  db_path = os.path.join(BASE_DIR, "overseerBumps.db")
  print(f"bumpstat() : trying to open connection. Path: '{db_path}'.")
  total = 0
  with sqlite3.Connection(db_path) as connection: 
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)")
    connection.commit()
    cursor.execute("SELECT * FROM BumpCount ORDER BY count")
    rows = cursor.fetchall()
    i = 1
    if rows is None:
      await interaction.response.send_message("No one has ever bumped the server. :(")
      return

    message = "```\nLeaderboard.\n\n"
    rows.reverse()
    for row in rows:
       if i == 11:
         break
       username = str(row[0])
       user = await overseer.fetch_user(row[0])
       if user:
         username = user.name
       total += row[1]
       message += f"{i}. {username} - {row[1]}.\n"
       i += 1
    total = total * 2
    total_days = total / 24
    total_days = round(total_days, 1)
    message += f"\nThe server was being bump'ed during over {total} hours or over {total_days} days!"
    message += "```"
    await interaction.response.send_message(message)

@overseer.event
async def on_message(message):
  if not message.interaction:
    print("on_message() : message is not an interaction.")
    return

  #print(f"on_message() : interaction name - '{message.interaction.name}', message author id - '{message.author.id}'")
  if message.interaction.name == "bump" and message.author.id == 302050872383242240:
    print("on_message() : message is a /bump command")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "overseerBumps.db")
    print(f"on_message() : trying to open connection. Path: '{db_path}'.")
    with sqlite3.Connection(db_path) as connection:
      cursor = connection.cursor()
      cursor.execute("CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)")
      connection.commit()
      cursor.execute("SELECT * FROM BumpCount WHERE userId = ?", [str(message.interaction.user.id)])
      row = cursor.fetchone()
      if row is None:
        print(f"bumpcheck() : the user is not in the DB yet, adding '{str(message.interaction.user.id)}'.")
        sql = f"INSERT INTO BumpCount(userId, count) VALUES (?, ?)"
        data = (str(message.interaction.user.id), 1)
        cursor.execute(sql, data)
      else:
        print(f"bumpcheck() : the user '{row[0]}' is in DB with '{row[1]}' bumps.")
        cursor.execute("UPDATE BumpCount SET count = count + 1 WHERE userId = ?", [str(message.interaction.user.id)])

      connection.commit()

@overseer.event
async def on_ready():
  print(f'Logged in as {overseer.user} (ID: {overseer.user.id})')
  print('------')
  await tree.sync(guild=discord.Object(id=768652124204433429))
  bumpcheck.start(overseer)

print("Connecting to Discord API...")
overseer.run(token)
