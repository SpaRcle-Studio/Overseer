import datetime
from src.config import *
import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import get
import sqlite3

class Bumpchecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     print("Bumpchecker cog is ready.")
    #     await self.bot.change_presence(activity=discord.Game(name="Bumping the server!"))
    #     await bumpcheck(self.bot)

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     if message.author.id == DISBOARD_USER_ID and message.content == "/bump":
    #         handle_bump(message)
async def bumpcheck(overseer):
    remind_message = f"Time to bump the server! :) ||<@&{BUMPER_ROLE_ID}>||"
    if not overseer:
        print("bumpcheck() : client object is not valid!")
        return

    bump_channel = overseer.get_channel(BUMP_CHANNEL_ID)
    if not bump_channel:
        print("bumpcheck() : channel object is not valid!")
        return

    latest_bump = None
    print("bumpcheck() : checking if remind is needed...")
    async for message in bump_channel.history(limit=200):
        if message.author.id == SELF_USER_ID and message.content == remind_message:
            print("bumpcheck() : remind is not needed, exiting the loop.")
            return

        interaction = message.interaction
        if not interaction:
            continue

        if interaction.name == "bump" and message.author.id == DISBOARD_USER_ID:
            latest_bump = message
            break

    if not latest_bump:
        print("bumpcheck() : failed to retrieve latest needed bump message!")
        return

    print(
        f"bumpcheck() : successfully retrieved latest needed bump message. It was created at: '{latest_bump.created_at}'."
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    difference = now - latest_bump.created_at
    difference_in_s = difference.total_seconds()
    minutes = divmod(difference_in_s, 60)[0]
    print(
        f"bumpcheck() : the difference between current time and the latest bump is '{minutes}' minutes. Left till next remind: '{120-minutes}'"
    )
    if minutes > 120:
        print("bumpcheck() : sending a remind message...")
        await bump_channel.send(remind_message)

# @TREE.command(
#     name="bumpstat",
#     description="Tells you how many times you /bumped the server.",
#     guild=discord.Object(id=768652124204433429),
# )
async def bumpstat(interaction):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "overseerBumps.db")
    print(f"bumpstat() : trying to open connection. Path: '{db_path}'.")
    with sqlite3.Connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)")
        connection.commit()
        print(f"bumpstat() searching for user with id: '{interaction.user.id}'.")
        cursor.execute(
            "SELECT * FROM BumpCount WHERE userId = ?",
            [str(interaction.user.id)],
        )
        row = cursor.fetchone()
        if row is None:
            await interaction.response.send_message(
                "You have never /bump'ed the server yet. Good luck next time!"
            )
        else:
            await interaction.response.send_message(
                f"```You have /bump'ed the server '{row[1]}' times!```"
            )

def handle_bump(message):
    print("on_message() : message is a /bump command")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "overseerBumps.db")
    print(f"on_message() : trying to open connection. Path: '{db_path}'.")
    with sqlite3.Connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)"
        )
        connection.commit()
        cursor.execute(
            "SELECT * FROM BumpCount WHERE userId = ?",
            [str(message.interaction.user.id)],
        )
        row = cursor.fetchone()
        if row is None:
            print(
                f"bumpcheck() : the user is not in the DB yet, adding '{str(message.interaction.user.id)}'."
            )
            sql = f"INSERT INTO BumpCount(userId, count) VALUES (?, ?)"
            data = (str(message.interaction.user.id), 1)
            cursor.execute(sql, data)
        else:
            print(f"bumpcheck() : the user '{row[0]}' is in DB with '{row[1]}' bumps.")
            cursor.execute(
                "UPDATE BumpCount SET count = count + 1 WHERE userId = ?",
                [str(message.interaction.user.id)],
            )

        connection.commit()

class SetBumpStatModal(discord.ui.Modal, title="Set user"):
    user_id = discord.ui.TextInput(
        label="Enter the user ID",
        placeholder="e.g., 1010130664269566064",
        required=True,
    )

    bump_value = discord.ui.TextInput(
        label="Enter the value",
        placeholder="e.g., 123",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "overseerBumps.db")
        print(f"bumpstat() : trying to open connection. Path: '{db_path}'.")
        with sqlite3.Connection(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS BumpCount (userId TEXT UNIQUE, count INTEGER)")
            connection.commit()
            sql = "INSERT INTO BumpCount(userId, count) VALUES (?, ?) ON CONFLICT(userId) DO UPDATE SET count=excluded.count"
            data = (self.user_id.value, self.bump_value.value)
            cursor.execute(sql, data)
        await interaction.response.send_message(
            f"Set bump stat for user `{self.user_id.value}` to `{self.bump_value.value}`",
            ephemeral=True
        )


# @TREE.command(
#     name="setbumpstat",
#     description="Set user's bump stat.",
#     guild=discord.Object(id=768652124204433429),
# )
async def setbumpstat(interaction):
    if interaction.user.id != 1010130664269566064:
        await interaction.response.send_message(content=f"This dude '{interaction.user.display_name}' tried to use /setbumpstat...\n\nOnly the God (innerviewer) is allowed to use this command!")
        return

    await interaction.response.send_modal(SetBumpStatModal())

# @TREE.command(
#     name="leaderboard",
#     description="Leaderboard of server's /bump'ers.",
#     guild=discord.Object(id=768652124204433429),
# )
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
            user = None# TODOawait OVERSEER.fetch_user(row[0])
            if user:
                username = user.name
            total += row[1]
            message += f"{i}. {username} - {row[1]}.\n"
            i += 1
        total = total * 2
        total_days = total / 24
        total_days = round(total_days, 1)
        message += (
            f"\nThe server was being bump'ed during over {total} hours or over {total_days} days!"
        )
        message += "```"
        await interaction.response.send_message(message)
