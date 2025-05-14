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

from src.config import *

from src.discord.bumpchecker import handle_bump, bumpcheck
from src.discord.dashboard_generator import DashboardGenerator
from src.discord.control_panel import ControlPanel
import src.utils as utils
from src.github.manager import GithubManager

from src.tokens import TokenManager

class OverseerDiscord(commands.Bot):
    tokens: TokenManager
    github_manager: GithubManager

    control_panel: ControlPanel

    def __init__(self, tokens: TokenManager, github_manager: GithubManager):
        intents = discord.Intents.all()
        super().__init__(command_prefix="*", intents=intents)

        self.tokens = tokens
        self.github_manager = github_manager
        #self.initial_extensions = ["src.discord.bumpchecker", "src.discord.control_panel"]
        #self.initial_extensions = ["src.discord.control_panel"]
        self.initial_extensions = []

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        guild = discord.Object(id=SPARCLE_SERVER_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    def startup(self):
        super().run(self.tokens.discord_token, reconnect=True)

    async def shutdown(self):
        await super().close()

    async def on_message(self, message):
        if not message.interaction:
            print("on_message() : message is not an interaction.")
            return

        # print(f"on_message() : interaction name - '{message.interaction.name}', message author id - '{message.author.id}'")
        if message.interaction.name == "bump" and message.author.id == DISBOARD_USER_ID:
            handle_bump(message)


    async def on_ready(self):
        print(f"Overseer logged in to Discord as {self.user}!")
        print("------")

        control_panel = ControlPanel(self, self.github_manager)
        await control_panel.initialize()
        #self.add_view(control_panel)

        #bumpcheck.start(OVERSEER)
