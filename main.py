import argparse
import datetime
import os
import sqlite3
import sys
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.utils import get

CONTROL_PANEL_CHANNEL_ID = 1371553026510159923
CONTROL_PANEL_MESSAGE_ID = 1371556019691589747
GITHUB_REPO = "SpaRcle-Studio/SREngine"
CONTROL_PANEL_CONTENT = "```Welcome to the Overseer Control Panel!```"

async def trigger_ci(interaction, branch):
    await interaction.response.defer(ephemeral=True)  # show loading spinner
    # Trigger GitHub workflow
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/MainCI.yml/dispatches"
    headers = {
        "Authorization": f"token {tokens['github_token']}",
        "Accept": "application/vnd.github+json"
    }
    json_data = { "ref": branch }  # branch to run on

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_data) as resp:
            if resp.status == 204:
                await interaction.followup.send("✅ CI workflow triggered!", ephemeral=True)
            elif resp.status == 422:
                await interaction.followup.send("😭 This branch does not exist!", ephemeral=True)
            else:
                text = await resp.text()
                await interaction.followup.send(f"❌ Failed to trigger CI. Status: {resp.status}\n{text}", ephemeral=True)

class ControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # timeout=None makes it persistent

    @discord.ui.button(
        label="Trigger CI!",
        style=discord.ButtonStyle.primary,
        custom_id="trigger_ci_button",
    )
    async def trigger_ci_button(self, interaction: discord.Interaction, button: discord.ui.Button, style=discord.ButtonStyle.primary):
        #await trigger_ci(interaction, "dev")
        await interaction.response.edit_message(content="```Choose a branch to trigger CI:```", view=TriggerCIView())


class TriggerCIView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="dev", style=discord.ButtonStyle.primary, custom_id="dev")
    async def dev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await trigger_ci(interaction, "dev")

    @discord.ui.button(label="master", style=discord.ButtonStyle.primary, custom_id="master")
    async def master(self, interaction: discord.Interaction, button: discord.ui.Button):
        await trigger_ci(interaction, "master")

    @discord.ui.button(label="Custom Branch", style=discord.ButtonStyle.secondary, custom_id="custom_branch")
    async def custom_branch(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CustomBranchModal())

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger, custom_id="back1")
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=CONTROL_PANEL_CONTENT, view=ControlPanel())

class CustomBranchModal(discord.ui.Modal, title="Enter the branch name!"):
    user_input = discord.ui.TextInput(
        label="Name:",
        style=discord.TextStyle.short,
        placeholder="Type something here...",
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        # This runs when user submits the modal
        input_value = self.user_input.value
        await trigger_ci(interaction, input_value)

@tasks.loop(minutes=5)
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

    print(
        f"bumpcheck() : successfully retrieved latest needed bump message. It was created at: '{message.created_at}'."
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    difference = now - message.created_at
    difference_in_s = difference.total_seconds()
    minutes = divmod(difference_in_s, 60)[0]
    print(
        f"bumpcheck() : the difference between current time and the latest bump is '{minutes}' minutes. Left till next remind: '{120-minutes}'"
    )
    if minutes > 120:
        print("bumpcheck() : sending a remind message...")
        await bump_channel.send(remind_message)


def get_tokens():
    print("get_tokens() : trying to get tokens from command line arguments...")
    parser = argparse.ArgumentParser("SpaRcle Overseer")
    parser.add_argument(
        "-discord_token",
        help="Provide the Discord token for the bot.",
        type=str,
        required=True,
        default="UNDEFINED",
    )
    parser.add_argument(
        "-github_token",
        help="Provide the GitHub token for the bot.",
        type=str,
        required=True,
        default="UNDEFINED",
    )

    result = {}

    args = parser.parse_args()
    if args.discord_token != "UNDEFINED":
        print("get_tokens() : Discord token is successfully retrieved.")
        result["discord_token"] = args.discord_token
    else:
        print("get_tokens() : Discord token is not provided, exiting.")
        sys.exit(1)

    if args.github_token != "UNDEFINED":
        print("get_tokens() : GitHub token is successfully retrieved.")
        result["github_token"] = args.github_token
    else:
        print("get_tokens() : GitHub token is not provided, exiting.")
        sys.exit(1)

    return result


print("Welcome to SpaRcle Overseer.")
print("Trying to get the token from environment variables...")
tokens = get_tokens()
intents = discord.Intents.all()
overseer = discord.Client(command_prefix="*", intents=intents)
tree = app_commands.CommandTree(overseer)


@tree.command(
    name="bumpstat",
    description="Tells you how many times you /bumped the server.",
    guild=discord.Object(id=768652124204433429),
)
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


@tree.command(
    name="leaderboard",
    description="Leaderboard of server's /bump'ers.",
    guild=discord.Object(id=768652124204433429),
)
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
        message += (
            f"\nThe server was being bump'ed during over {total} hours or over {total_days} days!"
        )
        message += "```"
        await interaction.response.send_message(message)


@overseer.event
async def on_message(message):
    if not message.interaction:
        print("on_message() : message is not an interaction.")
        return

    # print(f"on_message() : interaction name - '{message.interaction.name}', message author id - '{message.author.id}'")
    if message.interaction.name == "bump" and message.author.id == 302050872383242240:
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


@overseer.event
async def on_ready():
    print(f"Logged in as {overseer.user} (ID: {overseer.user.id})")
    print("------")

    overseer.add_view(ControlPanel())

    channel = overseer.get_channel(CONTROL_PANEL_CHANNEL_ID)
    if CONTROL_PANEL_MESSAGE_ID is None:
            message = await channel.send(CONTROL_PANEL_CONTENT, view=ControlPanel())
            print(f"Message ID: {message.id}")
            # TODO: save message id in the db
    else:
        message = await channel.fetch_message(CONTROL_PANEL_MESSAGE_ID)
        print(f"Message ID: {message.id}")
        await message.edit(content=CONTROL_PANEL_CONTENT, view=ControlPanel())

    await tree.sync(guild=discord.Object(id=768652124204433429))
    bumpcheck.start(overseer)


print("Connecting to Discord API...")
overseer.run(tokens["discord_token"])
