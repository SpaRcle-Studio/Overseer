import discord
import aiohttp
from discord.ext import commands

from src.tokens import TokenManager
from src.config import *
from src.discord.dashboard_generator import DashboardGenerator
from src.github.manager import GithubManager

class ControlPanel(discord.ui.View):
    bot: commands.Bot
    tokens: TokenManager
    control_message: discord.Message

    def __init__(self, bot: commands.Bot, github_manager: GithubManager):
        super().__init__(timeout=None)  # timeout=None makes it persistent

        self.bot = bot
        self.github_manager = github_manager
        self.trigger_ci_view = None

    async def initialize(self):
        control_channel = self.bot.get_channel(CONTROL_PANEL_CHANNEL_ID)
        if not isinstance(control_channel, discord.TextChannel):
            print(f"ControlPanel::initialize() : control channel is not a TextChannel. Type: {type(control_channel)}")
            return

        if CONTROL_PANEL_MESSAGE_ID is None:
                message = await control_channel.send(CONTROL_PANEL_CONTENT, view=self)
                print(f"ControlPanel::initialize(): sending message. ID: {message.id}")
                # TODO: save message id in the db?
        else:
            message = await control_channel.fetch_message(CONTROL_PANEL_MESSAGE_ID)
            print(f"ControlPanel::initialize() : message found. ID: {message.id}")
            await message.edit(content=CONTROL_PANEL_CONTENT, view=self)

        self.control_message = message

        #asd = DashboardGenerator(self.tokens, GITHUB_REPO, CACHE_DIR)
        #asd.generate_image()

    @discord.ui.button(
        label="Trigger CI!",
        style=discord.ButtonStyle.primary,
        custom_id="trigger_ci_button",
    )
    async def trigger_ci_button(self, interaction: discord.Interaction, button: discord.ui.Button, style=discord.ButtonStyle.primary):
        if not await self.is_authorized(interaction):
            return

        self.trigger_ci_view = TriggerCIView(self, self.control_message)
        await self.trigger_ci_view.process()

    @staticmethod
    async def is_authorized(interaction: discord.Interaction):
        authorized = isinstance(interaction.user, discord.Member) and interaction.user.get_role(SPARCLE_ROLE_ID) is not None
        if not authorized:
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)

        return authorized

class WorkflowButton(discord.ui.Button):
    def __init__(self, repo: str, branch: str, workflow_file: str, github_manager: GithubManager, style=discord.ButtonStyle.primary):
        super().__init__(label=workflow_file, style=style)

        self.repo = repo
        self.branch = branch
        self.workflow_file = workflow_file
        self.github_manager = github_manager

    async def callback(self, interaction: discord.Interaction):
        if not await ControlPanel.is_authorized(interaction):
            return

        resp = await self.github_manager.trigger_workflow(GITHUB_USER, self.repo, self.branch, self.workflow_file)
        if resp.status == 204:
            await interaction.followup.send("✅ CI workflow triggered!", ephemeral=True)
        elif resp.status == 422:
            await interaction.followup.send("😭 This branch does not exist!", ephemeral=True)
        else:
            text = await resp.text()
            await interaction.followup.send(f"❌ Failed to trigger CI. Status: {resp.status}\n{text}", ephemeral=True)

class GeneralControlButton(discord.ui.Button):
    def __init__(self, label, on_click, style=discord.ButtonStyle.primary):
        super().__init__(label=label, style=style)
        self.on_click = on_click

    async def callback(self, interaction: discord.Interaction):
        if not await ControlPanel.is_authorized(interaction):
            return

        await self.on_click(interaction)


class TriggerCIView(discord.ui.View):
    def __init__(self, control_panel: ControlPanel, message: discord.Message):
        super().__init__(timeout=None)
        self.control_panel = control_panel
        self.message = message

        self.repo = None
        self.branch = None
        self.workflow_file = None

    def remove_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if not item.custom_id in ["def-custom", "def-back"]:
                    item.disabled = True

    async def process(self):
        if self.repo is None:
            print("TriggerCIView::process() : repo stage.")
            self.remove_buttons()

            await self.message.edit(content="```Choose a repository to trigger CI:```", view=self)
            repos = self.control_panel.github_manager.get_active_repos(GITHUB_USER)
            if not repos:
                await self.message.edit(content="No active repositories found.", view=self)
                return

            for repo in repos:
                async def repo_callback(interaction, repo_name=repo.name, view: TriggerCIView = self):
                    view.repo = repo_name
                    await view.process()

                button = GeneralControlButton(repo.name, repo_callback)
                self.add_item(button)

        await self.message.edit(content="```Choose a branch to trigger CI:```", view=self)

        if self.repo and self.branch is None:
            print("TriggerCIView::process() : branch stage.")
            self.remove_buttons()

            await self.message.edit(content="```Choose a branch to trigger CI:```", view=self)
            branches = self.control_panel.github_manager.get_active_branches(GITHUB_USER, self.repo)
            if not branches:
                await self.message.edit(content="No branches found.", view=self)
                return

            for branch in branches:
                async def branch_callback(interaction, branch_name=branch.name, view: TriggerCIView = self):
                    view.branch = branch_name
                    await view.process()

                button = GeneralControlButton(branch.name, branch_callback)
                self.add_item(button)

        if self.repo and self.branch:
            print("TriggerCIView::process() : workflow stage.")
            self.remove_buttons()

            await self.message.edit(content="```Choose a workflow to trigger CI:```", view=self)
            workflows = self.control_panel.github_manager.get_triggerable_workflows(GITHUB_USER, self.repo)
            if not workflows:
                await self.message.edit(content="No workflows found.", view=self)
                return

            for workflow in workflows:
                async def workflow_callback(interaction, workflow_name=workflow.name, view: TriggerCIView = self):
                    view.workflow_file = workflow_name
                    await view.process()

                button = WorkflowButton(self.repo, self.branch, workflow.name, self.control_panel.github_manager)
                self.add_item(button)



    @discord.ui.button(label="Custom", style=discord.ButtonStyle.secondary, custom_id="def-custom")
    async def custom_branch(self, interaction: discord.Interaction, button: discord.ui.Button):
        def modal_callback(value, view=self):
            if not view.repo:
                view.repo = value
            elif not view.branch:
                view.branch = value
            elif not view.workflow_file:
                view.workflow_file = value

        await interaction.response.send_modal(Modal(modal_callback))

    @discord.ui.button(label="Back", style=discord.ButtonStyle.danger, custom_id="def-back")
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.workflow_file:
            self.workflow_file = None
        elif self.branch:
            self.branch = None
        elif self.repo:
            self.repo = None

        print("Back button pressed")
        await self.process()

class Modal(discord.ui.Modal, title="Enter the custom value!"):
    user_input = discord.ui.TextInput(
        label="Value:",
        style=discord.TextStyle.short,
        placeholder="Type something here...",
        required=True,
        max_length=100
    )

    def __init__(self, modal_callback):
        super().__init__()
        self.modal_callback = modal_callback

    async def on_submit(self, interaction: discord.Interaction):
        self.modal_callback(self.user_input.value)
